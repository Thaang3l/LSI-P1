#!/usr/bin/env python3
"""Replica la limpieza final de la VM LSI en otra VM Debian 13 equivalente.

El modo predeterminado es una simulacion. El modo aplicar crea un respaldo,
valida SSH y APT, muestra las transacciones y exige confirmacion interactiva.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


ENV = dict(os.environ, LC_ALL="C", LANG="C")

SERVICES_TO_MASK = (
    "ModemManager.service",
    "apparmor.service",
    "avahi-daemon.service",
    "avahi-daemon.socket",
    "e2scrub_reap.service",
    "exim4.service",
)

# Seleccion que se retiro en la VM original. Solo se incluyen paquetes
# instalados o con configuracion residual en la maquina que ejecute el script.
DESKTOP_PACKAGES = set("""
task-desktop task-gnome-desktop gdm3 firefox-esr firefox-esr-l10n-es-es
baobab cheese eog evince evince-common file-roller nautilus nautilus-data
nautilus-extension-gnome-terminal orca caribou seahorse simple-scan
synaptic software-properties-gtk transmission-gtk transmission-common
totem totem-common totem-plugins rhythmbox rhythmbox-data
rhythmbox-plugin-cdrecorder rhythmbox-plugins shotwell shotwell-common
rygel rygel-playbin rygel-tracker lightsoff swell-foop quadrapassel tali
aisleriot four-in-a-row hitori iagno five-or-more hoichess
gnome-games gnome-2048 gnome-chess gnome-klotski gnome-mahjongg
gnome-mines gnome-nibbles gnome-robots gnome-sudoku gnome-taquin gnome-tetravex
gnome-backgrounds gnome-calculator gnome-characters gnome-clocks
gnome-color-manager gnome-control-center gnome-control-center-data
gnome-disk-utility gnome-font-viewer gnome-logs gnome-music
gnome-online-miners gnome-remote-desktop gnome-screenshot
gnome-session gnome-session-bin gnome-session-common gnome-shell
gnome-shell-common gnome-shell-extensions gnome-software gnome-software-common
gnome-sound-recorder gnome-system-monitor gnome-terminal gnome-terminal-data
gnome-user-docs gnome-user-share gnome-weather
libreoffice libreoffice-writer libreoffice-calc libreoffice-impress
libreoffice-draw libreoffice-math libreoffice-base libreoffice-base-core
libreoffice-common libreoffice-core libreoffice-gnome libreoffice-gtk3
libreoffice-help-common libreoffice-help-en-us libreoffice-help-es
libreoffice-l10n-es libreoffice-style-colibre libreoffice-style-elementary
libreoffice-avmedia-backend-gstreamer libreofficekit-data
""".split())

# Estos paquetes tambien desaparecieron tras el autoremove de la VM original.
# Se solicitan expresamente para obtener un resultado reproducible.
EXTRA_PACKAGES = set("""
network-manager wpasupplicant fwupd power-profiles-daemon accountsservice
libnss-myhostname unzip 7zip jq udisks2 upower rtkit-daemon geoclue-2.0
colord packagekit bolt iio-sensor-proxy bluez
""".split())

RESIDUAL_CUPS = set("""
cups cups-browsed cups-core-drivers cups-daemon cups-filters
""".split())

PROTECTED_PACKAGES = (
    "openssh-server", "openssh-client", "ifupdown", "systemd", "systemd-sysv",
    "linux-image-amd64", "initramfs-tools", "grub-pc", "sudo", "rsyslog",
    "cron", "open-vm-tools", "apt", "dpkg",
)

HOOKS = (
    "/etc/network/if-pre-up.d/wireless-tools",
    "/etc/network/if-pre-up.d/wpasupplicant",
    "/etc/network/if-pre-up.d/ethtool",
    "/etc/network/if-up.d/resolved",
    "/etc/network/if-up.d/wpasupplicant",
    "/etc/network/if-up.d/ethtool",
    "/etc/network/if-up.d/avahi-autoipd",
)


def run(args, check=True):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=ENV)
    if check and result.returncode:
        raise RuntimeError("Fallo: " + " ".join(args) + "\n" + result.stdout)
    return result.stdout


def require_root_debian13():
    if os.geteuid() != 0:
        raise RuntimeError("Ejecuta el script como root dentro de la VM.")
    release = Path("/etc/os-release").read_text(errors="replace")
    if "ID=debian" not in release and 'ID="debian"' not in release:
        raise RuntimeError("Este script solo esta preparado para Debian.")
    if 'VERSION_ID="13"' not in release and "VERSION_ID=13" not in release:
        raise RuntimeError("La VM debe estar ya actualizada a Debian 13.")


def validate_base():
    run(["/usr/sbin/sshd", "-t"])
    if run(["systemctl", "is-active", "ssh.service"], check=False).strip() != "active":
        raise RuntimeError("ssh.service no esta activo; no se aplica la limpieza.")
    if run(["dpkg", "--audit"]).strip():
        raise RuntimeError("dpkg tiene operaciones pendientes.")
    run(["apt-get", "check"])
    interfaces = run(["ifquery", "--list", "--exclude=lo"], check=False).split()
    if not interfaces:
        raise RuntimeError("ifupdown no encuentra interfaces configuradas aparte de lo.")
    return interfaces


def package_states():
    output = run(["dpkg-query", "-W", "-f=${binary:Package}\t${db:Status-Abbrev}\n"],
                 check=False)
    return {line.split("\t", 1)[0].split(":", 1)[0]: line.split("\t", 1)[1]
            for line in output.splitlines() if "\t" in line}


def selected_packages():
    states = package_states()
    wanted = DESKTOP_PACKAGES | EXTRA_PACKAGES | RESIDUAL_CUPS
    return sorted(p for p in wanted if states.get(p, "")[:2] in ("ii", "rc"))


def apt_simulation(packages):
    if not packages:
        return "No hay paquetes de la seleccion instalados.\n", []
    out = run(["apt-get", "-s", "purge", *packages])
    removals = [line.split()[1].split(":", 1)[0]
                for line in out.splitlines() if line.startswith(("Remv ", "Purg "))]
    protected = sorted(set(removals) & set(PROTECTED_PACKAGES))
    if any(line.startswith("Inst ") for line in out.splitlines()):
        protected.append("[APT propone instalar o actualizar paquetes]")
    return out, protected


def make_backup():
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    root = Path("/root/lsi-limpieza-completa") / stamp
    root.mkdir(parents=True, mode=0o700)
    for name, command in (
        ("paquetes.tsv", ["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Abbrev}\n"]),
        ("manuales.txt", ["apt-mark", "showmanual"]),
        ("unidades.txt", ["systemctl", "list-unit-files", "--no-pager"]),
        ("interfaces.txt", ["cat", "/etc/network/interfaces"]),
        ("arranque.txt", ["systemd-analyze", "time"]),
    ):
        (root / name).write_text(run(command, check=False))
    with tarfile.open(root / "configuracion-antes.tar.gz", "w:gz") as archive:
        for source in ("/etc", "/var/lib/dpkg/status", "/var/lib/apt/extended_states"):
            if Path(source).exists():
                archive.add(source, arcname=source.lstrip("/"))
    return root


def plan():
    interfaces = validate_base()
    packages = selected_packages()
    simulation, protected = apt_simulation(packages)
    print("=== SIMULACION: NO SE MODIFICA NADA ===")
    print("Interfaces de ifupdown:", " ".join(interfaces))
    print("\nPaquetes seleccionados:\n", " ".join(packages) or "ninguno")
    print("\nSimulacion de APT:\n" + simulation)
    if protected:
        print("BLOQUEO: la transaccion afecta elementos protegidos:", ", ".join(protected))
    print("\nServicios que quedarian bloqueados:")
    for unit in SERVICES_TO_MASK:
        print(f"  {unit}: {run(['systemctl', 'is-enabled', unit], check=False).strip()}")
    print("\nHooks existentes que se apartarian:")
    for hook in HOOKS:
        if Path(hook).exists() or Path(hook).is_symlink():
            print(" ", hook)
    print("\nTambien se aplicarian multi-user.target, el ajuste de ifupdown-pre,")
    print("las mascaras de cups-filters/hdparm y el blacklist de la VM.")
    return bool(protected)


def audit():
    """Compara el equipo con el estado final conocido de la VM original."""
    differences = []
    states = package_states()
    for package in sorted(DESKTOP_PACKAGES | EXTRA_PACKAGES | RESIDUAL_CUPS):
        if states.get(package, "").startswith("ii"):
            differences.append("PAQUETE PRESENTE: " + package)
    for package in PROTECTED_PACKAGES:
        if not states.get(package, "").startswith("ii"):
            differences.append("PAQUETE ESENCIAL AUSENTE: " + package)
    for unit in SERVICES_TO_MASK:
        state = run(["systemctl", "is-enabled", unit], check=False).strip()
        if state not in ("masked", "masked-runtime"):
            differences.append(f"SERVICIO NO BLOQUEADO: {unit} ({state})")
    if run(["systemctl", "get-default"], check=False).strip() != "multi-user.target":
        differences.append("DESTINO: default.target no apunta a multi-user.target")
    for hook in HOOKS:
        if Path(hook).exists() or Path(hook).is_symlink():
            differences.append("HOOK TODAVIA ACTIVO: " + hook)
    for target_name in ("/etc/modules-load.d/cups-filters.conf",
                        "/etc/udev/rules.d/85-hdparm.rules"):
        target = Path(target_name)
        if not (target.is_symlink() and os.readlink(target) == "/dev/null"):
            differences.append("MASCARA DE ARCHIVO AUSENTE: " + target_name)
    blacklist = Path("/etc/modprobe.d/90-lsi-vm.conf")
    expected = {"blacklist intel_uncore", "blacklist intel_cstate", "blacklist sb_edac"}
    actual = set(blacklist.read_text().splitlines()) if blacklist.exists() else set()
    if not expected.issubset(actual):
        differences.append("BLACKLIST INCOMPLETA: /etc/modprobe.d/90-lsi-vm.conf")
    override = Path("/etc/systemd/system/ifupdown-pre.service.d/90-lsi-red.conf")
    if not override.exists():
        differences.append("AJUSTE DE RED AUSENTE: " + str(override))
    if differences:
        print("DIFERENCIAS CON EL ESTADO FINAL CONOCIDO:")
        print("\n".join("- " + item for item in differences))
        return 1
    print("El estado de limpieza conocido coincide.")
    print("Esto compara paquetes, mascaras y archivos de la limpieza; no compara")
    print("usuarios, IP, credenciales, contenido del bot ni todos los archivos del sistema.")
    return 0


def write_text(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)


def apply():
    interfaces = validate_base()
    packages = selected_packages()
    simulation, protected = apt_simulation(packages)
    print(simulation)
    if protected:
        raise RuntimeError("APT afectaria paquetes protegidos: " + ", ".join(protected))
    print("Esta operacion purgara el escritorio y aplicara los ajustes de la VM original.")
    print("La red seguira bajo ifupdown y SSH se conserva.")
    if input("Escribe APLICAR para continuar: ").strip() != "APLICAR":
        raise RuntimeError("Operacion cancelada.")

    backup = make_backup()
    print("Respaldo creado en", backup, flush=True)

    # Evita que APT considere prescindible la base necesaria para acceso remoto.
    installed = package_states()
    protect = [p for p in PROTECTED_PACKAGES if installed.get(p, "").startswith("ii")]
    if protect:
        run(["apt-mark", "manual", *protect])

    if packages:
        subprocess.run(["apt-get", "purge", *packages], env=ENV, check=True)
        # Replica el autoremove que se ejecuto en la VM original, pero vuelve a
        # simular y bloquea cualquier retirada de la base protegida.
        auto_sim = run(["apt-get", "-s", "autoremove", "--purge"])
        (backup / "simulacion-autoremove.txt").write_text(auto_sim)
        removals = {line.split()[1].split(":", 1)[0] for line in auto_sim.splitlines()
                    if line.startswith(("Remv ", "Purg "))}
        danger = sorted(removals & set(PROTECTED_PACKAGES))
        if danger:
            raise RuntimeError("No se ejecuta autoremove; propone retirar: " + ", ".join(danger))
        subprocess.run(["apt-get", "autoremove", "--purge"], env=ENV, check=True)

    run(["systemctl", "set-default", "multi-user.target"])
    for unit in SERVICES_TO_MASK:
        if run(["systemctl", "show", "-p", "LoadState", "--value", unit],
               check=False).strip() != "not-found":
            run(["systemctl", "mask", unit])

    iface_paths = " ".join("/sys/class/net/" + name for name in interfaces)
    wait_override = ("[Service]\nExecStart=\n"
                     "ExecStart=/bin/sh -c '/bin/udevadm wait --timeout=30 "
                     + iface_paths + " || /bin/udevadm settle --timeout=120'\n")
    write_text(Path("/etc/systemd/system/ifupdown-pre.service.d/90-lsi-red.conf"),
               wait_override)

    hook_backup = backup / "hooks-red-retirados"
    hook_backup.mkdir(mode=0o700)
    for hook_name in HOOKS:
        hook = Path(hook_name)
        if hook.exists() or hook.is_symlink():
            destination = hook_backup / (hook.parent.name + "--" + hook.name)
            shutil.move(str(hook), str(destination))

    # Conservar copias de cualquier archivo local reemplazado por /dev/null.
    for target_name in ("/etc/modules-load.d/cups-filters.conf",
                        "/etc/udev/rules.d/85-hdparm.rules"):
        target = Path(target_name)
        if (target.exists() or target.is_symlink()) and not (
                target.is_symlink() and os.readlink(target) == "/dev/null"):
            shutil.move(str(target), str(backup / ("original-" + target.name)))
        if target.exists() or target.is_symlink():
            target.unlink()
        target.symlink_to("/dev/null")

    write_text(Path("/etc/modprobe.d/90-lsi-vm.conf"),
               "blacklist intel_uncore\nblacklist intel_cstate\nblacklist sb_edac\n")

    cups_backup = backup / "logrotate-cups"
    for cups_file in Path("/etc/logrotate.d").glob("cups*"):
        cups_backup.mkdir(mode=0o700, exist_ok=True)
        shutil.move(str(cups_file), str(cups_backup / cups_file.name))

    run(["systemctl", "daemon-reload"])
    run(["update-initramfs", "-u", "-k", run(["uname", "-r"]).strip()])
    run(["/usr/sbin/sshd", "-t"])
    print("\nLimpieza aplicada. No se ha reiniciado la VM.")
    print("Respaldo:", backup)
    print("Comprueba systemctl --failed, ip route y una segunda sesion SSH antes de reboot.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", nargs="?", default="plan",
                        choices=("plan", "aplicar", "auditar"))
    args = parser.parse_args()
    require_root_debian13()
    os.umask(0o077)
    if args.modo == "plan":
        sys.exit(2 if plan() else 0)
    if args.modo == "auditar":
        sys.exit(audit())
    apply()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit("ERROR: " + str(error))
