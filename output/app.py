#Turbo or not? A small app for used-car buyers, built on the pipeline's final tables.

# Run the pipeline first, then:
#streamlit run output/app.py

from pathlib import Path

import duckdb
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "turbo.duckdb"
MIN_DRIVERS_PER_GROUP = 30   # a class needs this many drivers of BOTH engine types to be compared
ENGINE_TYPES = ["Turbocharged", "Naturally aspirated"]

st.set_page_config(page_title="Turbo or not?", page_icon="🚗")


# Loading data
@st.cache_data
def load(table):
    # Read one final table from the database into a DataFrame cached
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.table(table).df()


def confidence(drivers):
    """How far to trust one car's real-world figure, based on how many drivers reported it."""
    if drivers >= 5:
        return "Moderate"
    if drivers >= 2:
        return "Low"
    return "Very low"


if not DB_PATH.exists():
    st.error("Database not found. Run `python pipeline.py` from the project folder first.")
    st.stop()

engine = load("final_engine_summary")
drivers = load("final_driver_comparison")
vehicles = load("final_vehicle_summary")


# Header
st.title("Turbo or not?")
st.write(
    "Small turbo engines often have better official MPG than bigger naturally aspirated ones. "
    "But do they deliver it on the road? This compares the official figures for 2015–2020 "
    "petrol cars with the real MPG reported by drivers."
)
st.caption(
    "**Gap** = how far a driver's real MPG lands from the official figure for their own mix of "
    "city and highway driving. +5% means they beat it, −5% means they fell short."
)

# Part 1: The big picture
st.header("1. Turbo vs naturally aspirated")

# Only offer classes with enough drivers of both engine types to compare fairly
by_class = engine[engine["vehicle_class"] != "All classes"]
counts = by_class.groupby("vehicle_class")["drivers"].agg(["min", "count"])
comparable = sorted(counts[(counts["count"] == 2) & (counts["min"] >= MIN_DRIVERS_PER_GROUP)].index)

choice = st.selectbox("Type of car", ["All classes"] + comparable)

selected = engine[engine["vehicle_class"] == choice].set_index("engine_type")
in_choice = drivers[~drivers["is_outlier"]]
if choice != "All classes":
    in_choice = in_choice[in_choice["vehicle_class"] == choice]

columns = st.columns(2)
for column, engine_type in zip(columns, ENGINE_TYPES):
    row = selected.loc[engine_type]
    gaps = in_choice.loc[in_choice["engine_type"] == engine_type, "gap_pct"]
    column.metric(f"{engine_type}: typical gap", f"{row['median_gap_pct']:+.1%}")
    column.caption(
        f"{int(row['drivers']):,} drivers, {int(row['vehicles']):,} cars. "
        f"{row['share_beating_official']:.0%} matched or beat the official figure. "
        f"Middle half of drivers: {gaps.quantile(0.25):+.0%} to {gaps.quantile(0.75):+.0%}."
    )

if choice == "All classes":
    st.info(
        "Both engine types land within about 1% of their official figures. The difference between "
        "them is small compared with how much individual drivers vary, so there's no meaningful "
        "turbo penalty."
    )

st.subheader("By type of car")
chart_data = by_class[by_class["vehicle_class"].isin(comparable)].assign(
    median_gap=lambda df: df["median_gap_pct"] * 100
)
st.bar_chart(
    chart_data,
    x="vehicle_class",
    y="median_gap",
    color="engine_type",
    stack=False,
    horizontal=True,
    x_label="Typical gap vs official figure (%)",
    y_label="",
)
st.caption(
    f"Only classes with at least {MIN_DRIVERS_PER_GROUP} drivers of each engine type are shown. "
    "The type of car matters more than the engine: small cars tend to beat their figures, "
    "SUVs and pickups tend to fall short."
)

# Part 2: compare two cars

st.header("2. Compare two cars")
st.write("Type to search, e.g. *2017 Honda Civic*.")

cars = vehicles[vehicles["drivers"] > 0].copy()
cars["label"] = (
    cars["model_year"].astype(str) + " " + cars["make"] + " " + cars["model"]
    + " – " + cars["engine_litres"].map("{:.1f}L".format) + " " + cars["engine_type"].str.lower()
    + ", " + cars["transmission"] + " [ID " + cars["vehicle_id"].astype(str) + "]"
)
cars = cars.sort_values("label").set_index("label")
labels = list(cars.index)

columns = st.columns(2)
for i, column in enumerate(columns):
    label = column.selectbox(f"Car {i + 1}", labels, index=min(i, len(labels) - 1), key=f"car_{i}")
    car = cars.loc[label]
    column.metric("Official combined MPG", f"{car['official_combined_mpg']:.1f}")
    column.metric("Real-world MPG (drivers)", f"{car['real_world_mpg']:.1f}")
    column.metric("Typical gap vs official", f"{car['median_gap_pct']:+.1%}")

    level = confidence(car["drivers"])
    message = f"Based on {int(car['drivers'])} driver(s): **{level.lower()} confidence**."
    if level == "Very low":
        column.warning(message + " Treat this as a single anecdote.")
    else:
        column.caption(message)

# Footer
st.divider()
st.caption(
    "Data: U.S. Department of Energy, fueleconomy.gov (US-market cars, used for non-commercial, "
    "educational purposes). Real-world figures are self-reported by drivers who chose to share "
    "them, who may drive more carefully than average. Outliers (more than 50% from the official "
    "figure) are excluded."
)