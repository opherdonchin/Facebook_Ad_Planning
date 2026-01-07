from dataclasses import dataclass
from typing import Callable, Dict
import pandas as pd
import ibis

# -------------------------
# Transform type
# -------------------------

TransformFn = Callable[[Dict[str, ibis.expr.types.Table]], pd.DataFrame]

# -------------------------
# Transform spec
# -------------------------


@dataclass(frozen=True)
class TransformSpec:
    name: str
    transform: TransformFn
    input_tables: Dict[str, str]  # alias -> Grist table id
    output_table: str
    overwrite: bool = True
    # mapping of input_alias -> { raw_column: canonical_column }
    select_rename: Dict[str, Dict[str, str]] = None


# -------------------------
# Transforms
# -------------------------


def weekly_metrics_transform(tables: Dict[str, ibis.expr.types.Table]) -> pd.DataFrame:
    t = tables["perf"]

    # Group to weekly ad level
    g = t.group_by(["Week", "Campaign", "Ad"]).aggregate(
        Spend=t["Spend"].sum(),
        Leads=t["Leads"].sum(),
    )
    # ... rest of function ... we'll use a NEW transform instead of modifying this one.


# -------------------------
# New transform for joined productions
# -------------------------


def weekly_metrics_joined_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    t_runs = tables["perf"]
    t_ads = tables["ads"]

    # Join logic: Weekly_runs.Ad (ref) == Ads.id
    # Note: Grist references come through as integers (row IDs)
    joined = t_runs.join(t_ads, t_runs["Ad"] == t_ads["id"])

    # Group by canonical names
    g = joined.group_by(
        [t_runs["Week"], t_ads["Campaign"], t_ads["Name"].name("Ad")]
    ).aggregate(
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
    )

    # Calculate metrics
    g = g.mutate(CPL=ibis.ifelse(g["Leads"] > 0, g["Spend"] / g["Leads"], ibis.null()))

    g = g.mutate(
        Flag_NoLeads=ibis.ifelse(g["Leads"] == 0, True, False),
        Flag_LowSample=ibis.ifelse(g["Leads"] < 3, True, False),
    )

    return g.execute()


# -------------------------
# Registry
# -------------------------

TRANSFORMS: Dict[str, TransformSpec] = {
    "weekly_metrics_test": TransformSpec(
        name="weekly_metrics_test",
        transform=weekly_metrics_transform,
        input_tables={
            "perf": "Test_ad_performance",
        },
        output_table="Scratch_Ads_Metrics",
        overwrite=True,
        select_rename={
            "perf": {
                "Week": "Week",
                "Campaign": "Campaign",
                "Ad": "Ad",
                "Spend": "Spend",
                "Leads": "Leads",
            }
        },
    ),
}

TRANSFORMS["weekly_metrics"] = TransformSpec(
    name="weekly_metrics",
    transform=weekly_metrics_joined_transform,
    input_tables={
        "perf": "Weekly_runs",
        "ads": "Ads",
    },
    output_table="Derived_Weekly_Ad_Metrics",
    overwrite=True,
    select_rename={
        "perf": {
            "Week": "Week",
            "Ad": "Ad",
            "Spend": "Spend",
            "Leads": "Leads",
        },
        "ads": {
            "id": "id",
            "Name": "Name",
            "Campaign": "Campaign",
        },
    },
)
