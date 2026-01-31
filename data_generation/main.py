"""CLI for data generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Literal, cast

import pandas as pd
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from data_generation.config import GenerationConfig
from data_generation.generators import (
    CustomerGenerator,
    DriverGenerator,
    LocationGenerator,
    PackageGenerator,
    TrackingEventGenerator,
    VehicleGenerator,
    WeatherGenerator,
)

app = typer.Typer(
    name="logistics",
    help="Synthetic data generation for logistics platform",
    add_completion=False,
)
console = Console()


def save_data(data: list[dict], output_dir: Path, name: str, format: str) -> Path:
    """Save generated data to file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "parquet":
        filepath = output_dir / f"{name}.parquet"
        df = pd.DataFrame(data)
        df.to_parquet(filepath, index=False)
    elif format == "csv":
        filepath = output_dir / f"{name}.csv"
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
    elif format == "json":
        filepath = output_dir / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported format: {format}")

    return filepath


@app.command()
def generate(
    packages: int = typer.Option(10000, "--packages", "-p", help="Number of packages to generate"),
    customers: int = typer.Option(5000, "--customers", "-c", help="Number of customers"),
    drivers: int = typer.Option(500, "--drivers", "-d", help="Number of drivers"),
    vehicles: int = typer.Option(300, "--vehicles", "-v", help="Number of vehicles"),
    locations: int = typer.Option(1000, "--locations", "-l", help="Number of locations"),
    output_dir: Path = typer.Option(Path("data/generated"), "--output", "-o", help="Output directory"),
    format: str = typer.Option("parquet", "--format", "-f", help="Output format (parquet, csv, json)"),
    seed: int = typer.Option(42, "--seed", "-s", help="Random seed for reproducibility"),
    start_date: str = typer.Option("2023-01-01", "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option("2024-12-31", "--end-date", help="End date (YYYY-MM-DD)"),
    include_weather: bool = typer.Option(False, "--weather", "-w", help="Generate weather data"),
) -> None:
    """Generate synthetic logistics data."""
    console.print("[bold blue]Logistics Data Platform - Data Generator[/bold blue]")
    console.print()

    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Create config
    config = GenerationConfig(
        num_packages=packages,
        num_customers=customers,
        num_drivers=drivers,
        num_vehicles=vehicles,
        num_locations=locations,
        output_dir=output_dir,
        output_format=cast(Literal["csv", "parquet", "json"], format),
        random_seed=seed,
        start_date=start,
        end_date=end,
    )

    # Show configuration
    config_table = Table(title="Generation Configuration")
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_row("Packages", f"{packages:,}")
    config_table.add_row("Customers", f"{customers:,}")
    config_table.add_row("Drivers", f"{drivers:,}")
    config_table.add_row("Vehicles", f"{vehicles:,}")
    config_table.add_row("Locations", f"{locations:,}")
    config_table.add_row("Date Range", f"{start_date} to {end_date}")
    config_table.add_row("Output Format", format)
    config_table.add_row("Output Directory", str(output_dir))
    config_table.add_row("Random Seed", str(seed))
    console.print(config_table)
    console.print()

    generated_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Generate locations first
        task = progress.add_task("[cyan]Generating locations...", total=None)
        location_gen = LocationGenerator(config)
        locations_data = location_gen.generate()
        hub_locations = location_gen.get_hub_locations()
        hub_location_ids = [loc["location_id"] for loc in hub_locations]
        location_ids = [loc["location_id"] for loc in locations_data]
        filepath = save_data(locations_data, output_dir, "locations", format)
        generated_files.append(("locations", len(locations_data), filepath))
        progress.update(task, completed=True)

        # Generate customers
        task = progress.add_task("[cyan]Generating customers...", total=None)
        customer_gen = CustomerGenerator(config)
        customers_data = customer_gen.generate()
        customer_ids = [c["customer_id"] for c in customers_data]
        filepath = save_data(customers_data, output_dir, "customers", format)
        generated_files.append(("customers", len(customers_data), filepath))
        progress.update(task, completed=True)

        # Generate drivers
        task = progress.add_task("[cyan]Generating drivers...", total=None)
        driver_gen = DriverGenerator(config, hub_location_ids)
        drivers_data = driver_gen.generate()
        driver_ids = [d["driver_id"] for d in drivers_data]
        filepath = save_data(drivers_data, output_dir, "drivers", format)
        generated_files.append(("drivers", len(drivers_data), filepath))
        progress.update(task, completed=True)

        # Generate vehicles
        task = progress.add_task("[cyan]Generating vehicles...", total=None)
        vehicle_gen = VehicleGenerator(config, hub_location_ids)
        vehicles_data = vehicle_gen.generate()
        vehicle_ids = [v["vehicle_id"] for v in vehicles_data]
        filepath = save_data(vehicles_data, output_dir, "vehicles", format)
        generated_files.append(("vehicles", len(vehicles_data), filepath))
        progress.update(task, completed=True)

        # Generate packages
        task = progress.add_task("[cyan]Generating packages...", total=None)
        package_gen = PackageGenerator(config, customer_ids, location_ids, hub_location_ids)
        packages_data = package_gen.generate()
        filepath = save_data(packages_data, output_dir, "packages", format)
        generated_files.append(("packages", len(packages_data), filepath))
        progress.update(task, completed=True)

        # Generate tracking events
        task = progress.add_task("[cyan]Generating tracking events...", total=None)
        event_gen = TrackingEventGenerator(
            config, packages_data, locations_data, hub_location_ids, driver_ids, vehicle_ids
        )
        events_data = event_gen.generate()
        filepath = save_data(events_data, output_dir, "tracking_events", format)
        generated_files.append(("tracking_events", len(events_data), filepath))
        progress.update(task, completed=True)

        # Generate weather data (optional)
        if include_weather:
            task = progress.add_task("[cyan]Generating weather data...", total=None)
            weather_gen = WeatherGenerator(config)
            weather_data = weather_gen.generate(locations_data)
            filepath = save_data(weather_data, output_dir, "weather", format)
            generated_files.append(("weather", len(weather_data), filepath))
            progress.update(task, completed=True)

    # Summary
    console.print()
    summary_table = Table(title="Generated Data Summary")
    summary_table.add_column("Dataset", style="cyan")
    summary_table.add_column("Records", style="green", justify="right")
    summary_table.add_column("File", style="dim")

    for name, count, filepath in generated_files:
        summary_table.add_row(name, f"{count:,}", str(filepath))

    console.print(summary_table)
    console.print()
    console.print("[bold green]✓ Data generation complete![/bold green]")


@app.command()
def upload(
    source_dir: Path = typer.Option(Path("data/generated"), "--source", "-s", help="Source directory"),
    bucket: str = typer.Option(..., "--bucket", "-b", help="GCS bucket name"),
    prefix: str = typer.Option("raw", "--prefix", "-p", help="GCS path prefix"),
) -> None:
    """Upload generated data to Google Cloud Storage."""
    from google.cloud import storage  # type: ignore[attr-defined]

    console.print(f"[bold blue]Uploading data to gs://{bucket}/{prefix}/[/bold blue]")

    client = storage.Client()
    bucket_obj = client.bucket(bucket)

    files = list(source_dir.glob("*"))
    if not files:
        console.print("[red]No files found in source directory[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for filepath in files:
            task = progress.add_task(f"[cyan]Uploading {filepath.name}...", total=None)
            blob = bucket_obj.blob(f"{prefix}/{filepath.name}")
            blob.upload_from_filename(str(filepath))
            progress.update(task, completed=True)

    console.print()
    console.print(f"[bold green]✓ Uploaded {len(files)} files to gs://{bucket}/{prefix}/[/bold green]")


@app.command()
def info() -> None:
    """Show information about the data generator."""
    console.print("[bold blue]Logistics Data Platform - Data Generator[/bold blue]")
    console.print()
    console.print("This tool generates synthetic logistics data for testing and development.")
    console.print()
    console.print("[bold]Available datasets:[/bold]")
    console.print("  • [cyan]packages[/cyan] - Package/shipment records")
    console.print("  • [cyan]tracking_events[/cyan] - Package tracking events")
    console.print("  • [cyan]customers[/cyan] - Customer information")
    console.print("  • [cyan]locations[/cyan] - Facilities and addresses")
    console.print("  • [cyan]drivers[/cyan] - Driver information")
    console.print("  • [cyan]vehicles[/cyan] - Fleet information")
    console.print("  • [cyan]weather[/cyan] - Weather conditions (optional)")
    console.print()
    console.print("[bold]Example usage:[/bold]")
    console.print("  logistics generate --packages 10000")
    console.print("  logistics generate -p 100000 -f csv --weather")
    console.print("  logistics upload --bucket my-bucket --prefix raw/2024")


if __name__ == "__main__":
    app()
