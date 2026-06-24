#!/usr/bin/env python3
# scripts/docker_deploy.py
import subprocess
import sys
import typer
from rich.console import Console
from rich.panel import Panel
import semver

app = typer.Typer(help="🛠️ CLI de Despliegue para MPH - UTIC")
console = Console()

IMAGE_NAME = "ledvirbau/document-ai-prototype"


def run_cmd(command: str, description: str):
    """Ejecuta un comando de shell y maneja errores con estilo."""
    try:
        console.print(f"[bold cyan]⏳ {description}[/bold cyan]")
        # Ejecutamos normalmente para ver los logs en vivo
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        console.print(
            Panel(
                f"[bold red]❌ Error en: {description}\nCódigo: {e.returncode}[/bold red]",
                border_style="red",
            )
        )
        sys.exit(1)


def check_docker_login():
    """Verifica si Docker está logueado, si no pide login."""
    try:
        subprocess.run(
            "docker info",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠️ No estás logueado en Docker Hub[/yellow]")
        run_cmd("docker login", "Autenticación Docker Hub requerida")


@app.command()
def deploy(
    version: str = typer.Argument(..., help="La versión a desplegar (ej. 1.3.0)"),
    latest: bool = typer.Option(
        True, "--no-latest", help="Evita etiquetar y subir como 'latest'"
    ),
    multiarch: bool = typer.Option(
        False,
        "--multiarch",
        help="Construir imagen para amd64 y arm64 (requiere buildx)",
    ),
):
    """
    Empaqueta y sube una nueva versión de la aplicación a Docker Hub.
    """
    # 1. Validar versión semántica
    try:
        semver.VersionInfo.parse(version)
    except ValueError:
        console.print(
            f"[bold red]❌ La versión '{version}' no es válida. Usa formato X.Y.Z (ej. 1.3.0)[/bold red]"
        )
        sys.exit(1)

    console.print(
        Panel.fit(
            f"[bold blue]🚀 Despliegue de Versión: {version}[/bold blue]\n[dim]Imagen: {IMAGE_NAME}[/dim]",
            border_style="blue",
        )
    )

    # 2. Verificar Docker login
    check_docker_login()

    # 3. Sincronizar dependencias
    run_cmd("uv sync", "Sincronizando dependencias (uv sync)")

    # 4. Construcción y Subida
    if multiarch:
        # Multiarch requiere buildx y subir directamente (--push)
        run_cmd(
            f"docker buildx build --platform linux/amd64,linux/arm64 -t {IMAGE_NAME}:{version} --push .",
            "Construyendo y subiendo versión Multi-arquitectura...",
        )
    else:
        # Build tradicional
        run_cmd(
            f"docker build -t {IMAGE_NAME}:{version} .",
            "Construyendo la imagen Docker...",
        )
        run_cmd(
            f"docker push {IMAGE_NAME}:{version}",
            f"Subiendo versión {version} a Docker Hub...",
        )

    # 5. Etiqueta Latest
    if latest:
        run_cmd(
            f"docker tag {IMAGE_NAME}:{version} {IMAGE_NAME}:latest && docker push {IMAGE_NAME}:latest",
            "Actualizando etiqueta 'latest'...",
        )
    else:
        console.print(
            "[bold dim]⏭️ Omitiendo etiqueta 'latest' (--no-latest detectado).[/bold dim]"
        )

    # 6. Resumen
    console.print(
        Panel(
            f"[bold green]✅ ¡Despliegue versión {version} completado con éxito![/bold green]",
            border_style="green",
        )
    )
    console.print("Para actualizar el servidor, ejecuta:")
    console.print(
        "  [bold cyan]docker-compose pull && docker-compose up -d[/bold cyan]\n"
    )


if __name__ == "__main__":
    app()
