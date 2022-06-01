"""Set up QIIME 2 on Google colab.

Do not use this on o local machine, especially not as an admin!
"""

import os
import sys
from subprocess import Popen, PIPE

r = Popen(["pip", "install", "rich"])
r.wait()
from rich.console import Console  # noqa
con = Console()

has_conda = "conda version" in os.popen("conda info").read()
has_qiime = "QIIME 2 release:" in os.popen("qiime info").read()


MINICONDA_PATH = (
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
)


def cleanup():
    """Remove downloaded files."""
    if os.path.exists("Miniconda3-latest-Linux-x86_64.sh"):
        os.remove("Miniconda3-latest-Linux-x86_64.sh")
    if os.path.exists("install-sra-tools.sh"):
        os.remove("install-sra-tools.sh")
    con.log("Cleaned up unneeded files.")


def run_and_check(
        args, check, message, failure, success, console=con, env_vars=None,
        check_returncode=True
):
    """Run a command and check that it worked."""
    console.log(message)
    env_vars = {**os.environ, **env_vars} if env_vars else os.environ
    r = Popen(args, env=env_vars, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    o, e = r.communicate()
    out = o + e

    if (check_returncode and r.returncode == 0 and check in out) or \
            (not check_returncode and check in out):
        console.log("[blue]%s[/blue]" % success)
    else:
        console.log("[red]%s[/red]" % failure, out)
        cleanup()
        sys.exit(1)


def _hack_in_the_plugins():
    """Add the plugins to QIIME."""
    import qiime2.sdk as sdk
    from importlib.metadata import entry_points

    pm = sdk.PluginManager(add_plugins=False)
    for entry in entry_points()["qiime2.plugins"]:
        plugin = entry.load()
        package = entry.value.split(':')[0].split('.')[0]
        pm.add_plugin(plugin, package, entry.name)


if __name__ == "__main__":
    if not has_conda:
        run_and_check(
            ["wget", MINICONDA_PATH],
            "saved",
            ":snake: Downloading miniconda...",
            "failed downloading miniconda :sob:",
            ":snake: Done."
        )

        run_and_check(
            ["bash", "Miniconda3-latest-Linux-x86_64.sh", "-bfp", "/usr/local"],
            "installation finished.",
            ":snake: Installing miniconda...",
            "could not install miniconda :sob:",
            ":snake: Installed miniconda to `/usr/local` :snake:"
        )
    else:
        con.log(":snake: Miniconda is already installed. Skipped.")

    if not has_qiime:
        run_and_check(
            ["conda", "install", "mamba", "-y", "-n", "base",
             "-c", "conda-forge"],
            "mamba",
            ":mag: Installing mamba...",
            "could not install mamba :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["mamba", "env", "update", "-n", "base", "--file",
             "environment.yml"],
            "To activate this environment, use",
            ":mag: Installing QIIME 2. This may take a little bit.\n :clock1:",
            "could not install QIIME 2 :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["pip", "install",
             "git+https://github.com/bokulich-lab/q2-fondue.git@cb924d43d1c217342911fc5c2eaf136d4d283fa4"],
            "Successfully installed",
            ":mag: Installing required plugins. "
            "This may take a little bit.\n :clock1:",
            "could not install some QIIME 2 plugins :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["wget", "--header", "Accept: application/vnd.github.v3.raw",
             "https://api.github.com/repos/bokulich-lab/q2-fondue/contents/install-sra-tools.sh"],
            "saved",
            ":mag: Fetching SRA-Tools installation script :clock1:",
            "could not fetch :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["chmod", "+x", "install-sra-tools.sh"],
            "",
            ":mag: Adjusting script permissions :clock1:",
            "could not change permissions :sob:",
            ":mag: Done."
        )

        run_and_check(
            ["bash", "install-sra-tools.sh"],
            "Configuration completed",
            ":mag: Installing SRA Tools :clock1:",
            "could not install SRA Tools :sob:",
            ":mag: Done.",
            env_vars={"CONDA_PREFIX": "/usr/local"}
        )

        run_and_check(
            ["vdb-config", "--root", "-s", "/repository/user/main/public/root=/content/prefetch_cache"],
            "",
            ":mag: Setting prefetch cache location :clock1:",
            "could not configure SRA Tools :sob:",
            ":mag: Done.",
            env_vars={"CONDA_PREFIX": "/usr/local"}
        )

        run_and_check(
            ["vdb-config", "--prefetch-to-user-repo"],
            "will download to User Repository",
            ":mag: Finalizing prefetch configuration :clock1:",
            "could not configure SRA Tools :sob:",
            ":mag: Done.",
            env_vars={"CONDA_PREFIX": "/usr/local"}
        )

        # this is a hack to make SRA tools work: this command fails but somehow
        # still manages to configure the toolkit properly
        run_and_check(
            ["vdb-config", "--interactive"],
            "SIGNAL",
            ":mag: Fixing SRA Tools configuration :clock1:",
            "could not configure SRA Tools :sob:",
            ":mag: Done.",
            env_vars={"CONDA_PREFIX": "/usr/local"},
            check_returncode=False
        )

        run_and_check(
            ["pip", "install", "empress"],
            "Successfully installed empress-",
            ":evergreen_tree: Installing Empress...",
            "could not install Empress :sob:",
            ":evergreen_tree: Done."
        )
    else:
        con.log(":mag: QIIME 2 is already installed. Skipped.")

    run_and_check(
        ["qiime", "info"],
        "QIIME 2 release:",
        ":bar_chart: Checking that QIIME 2 command line works...",
        "QIIME 2 command line does not seem to work :sob:",
        ":bar_chart: QIIME 2 command line looks good :tada:"
    )

    run_and_check(
        ["prefetch", "--help"],
        "Usage: prefetch",
        ":bar_chart: Checking that SRA Toolkit works...",
        "SRA Toolkit does not seem to work :sob:",
        ":bar_chart: SRA Toolkit looks good :tada:"
    )

    if sys.version_info[0:2] == (3, 8):
        sys.path.append("/usr/local/lib/python3.8/site-packages")
        con.log(":mag: Fixed import paths to include QIIME 2.")

        con.log(":bar_chart: Checking if QIIME 2 import works...")
        try:
            import qiime2  # noqa
        except Exception:
            con.log("[red]QIIME 2 can not be imported :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: QIIME 2 can be imported :tada:[/blue]")

        con.log(":bar_chart: Setting up QIIME 2 plugins...")
        try:
            _hack_in_the_plugins()
            from qiime2.plugins import feature_table # noqa
        except Exception:
            con.log("[red]Could not add the plugins :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: Plugins are working :tada:[/blue]")

    cleanup()

    con.log("[green]Everything is A-OK. "
            "You can start using QIIME 2 now :thumbs_up:[/green]")
