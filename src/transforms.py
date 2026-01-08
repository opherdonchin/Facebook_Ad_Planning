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


def weekly_metrics_joined_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    t_runs = tables['perf']
    t_ads = tables['ads']

    # Canonical inputs:
    # perf: Week, Ad_id, Spend, Leads
    # ads: id, Name, Campaign

    joined = t_runs.join(t_ads, t_runs['Ad_id'] == t_ads['id'])

    # Group by canonical names
    g = joined.group_by(
        [t_runs['Week'], t_ads['Campaign'], t_ads['Name'].name('Ad')]
    ).aggregate(
        Spend=t_runs['Spend'].sum(),
        Leads=t_runs['Leads'].sum(),
    )

    # Calculate metrics
    g = g.mutate(
        CPL=ibis.ifelse(g['Leads'] > 0, g['Spend'] / g['Leads'], ibis.null())
    )

    g = g.mutate(
        Flag_NoLeads=ibis.ifelse(g['Leads'] == 0, True, False),
        Flag_LowSample=ibis.ifelse(g['Leads'] < 3, True, False),
    )

    return g.execute()


def lifetime_ad_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    t_runs = tables['perf']
    t_ads = tables['ads']

    # Canonical inputs:
    # perf: Week, Ad_id, Spend, Leads
    # ads: id, Name, Campaign

    # 1. Aggregate Weekly_runs by Ad_id
    # Note: Weeks is count distinct of Week
    metrics = t_runs.group_by(t_runs['Ad_id']).aggregate(
        Spend=t_runs['Spend'].sum(),
        Leads=t_runs['Leads'].sum(),
        Weeks=t_runs['Week'].nunique(),
        FirstWeek=t_runs['Week'].min(),
        LastWeek=t_runs['Week'].max(),
    )

    # 2. Join to Ads for metadata
    joined = metrics.join(t_ads, metrics['Ad_id'] == t_ads['id'])

    # 3. Project and formatting
    res = joined.select(
        t_ads['Campaign'],
        t_ads['Name'].name('Ad'),
        metrics['Spend'],
        metrics['Leads'],
        metrics['Weeks'],
        metrics['FirstWeek'],
        metrics['LastWeek'],
    )
    
    # Calculate CPL
    res = res.mutate(
        CPL=ibis.ifelse(res['Leads'] > 0, res['Spend'] / res['Leads'], ibis.null())
    )

    return res.execute()


def tag_lifetime_rollups_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    # Inputs
    t_perf = tables['perf']
    t_ads = tables['ads']
    t_creatives = tables['creatives']
    t_media = tables['media']
    t_headlines = tables['headlines']
    t_texts = tables['texts']

    # Dictionaries
    d_style = tables['media_style']
    d_energy = tables['media_energy']
    d_tone = tables['tone']
    d_promise = tables['promise_types']
    d_hook = tables['hook_types']

    # 1. Build Spine
    # Use uniquely named IDs (from select_rename) to avoid join collisions in Ibis
    
    spine = (
        t_perf.join(t_ads, t_perf['Ad_id'] == t_ads['ad_oid'])
        .join(t_creatives, t_ads['Creative_id'] == t_creatives['creative_oid'])
        .join(t_media, t_creatives['Media_id'] == t_media['media_oid'])
        .join(t_headlines, t_creatives['Headline_id'] == t_headlines['headline_oid'])
        .join(t_texts, t_ads['Text_id'] == t_texts['text_oid'])
    )

    # Helper to aggregate by a tag column
    def agg_by_tag(spine_table, tag_col_expr, dim_name):
        return (
            spine_table.group_by(tag_col_expr.name('Tag'))
            .aggregate(
                Spend=spine_table['Spend'].sum(),
                Leads=spine_table['Leads'].sum(),
                Ads=spine_table['Ad_id'].nunique(),
                Weeks=spine_table['Week'].nunique(),
            )
            .mutate(
                Tag_Dimension=ibis.literal(dim_name),
                CPL=lambda t: ibis.ifelse(t.Leads > 0, t.Spend / t.Leads, ibis.null()),
            )
            # Filter null tags
            .filter(lambda t: t.Tag.notnull())
            .filter(lambda t: t.Tag != '')
            .select('Tag_Dimension', 'Tag', 'Spend', 'Leads', 'CPL', 'Ads', 'Weeks')
        )

    unions = []

    # 1. Media_Style
    s_style = spine.join(d_style, spine['Media_Style_id'] == d_style['style_oid'])
    unions.append(agg_by_tag(s_style, d_style['Media_Style'], 'Media_Style'))

    # 2. Media_Energy
    s_en = spine.join(d_energy, spine['Media_Energy_id'] == d_energy['energy_oid'])
    unions.append(agg_by_tag(s_en, d_energy['Media_Energy'], 'Media_Energy'))

    # 3. Headline_Tone
    s_tone = spine.join(d_tone, spine['Tone_id'] == d_tone['tone_oid'])
    unions.append(agg_by_tag(s_tone, d_tone['Tone'], 'Headline_Tone'))

    # 4. Headline_Promise
    s_hp = spine.join(d_promise, spine['Promise_id_headline'] == d_promise['promise_oid'])
    unions.append(agg_by_tag(s_hp, d_promise['Promise'], 'Headline_Promise'))

    # 5. Headline_Hook
    s_hh = spine.join(d_hook, spine['Hooks_id'] == d_hook['hook_oid'])
    unions.append(agg_by_tag(s_hh, d_hook['Hook'], 'Headline_Hook'))

    # 6. Text_Hook
    s_th = spine.join(d_hook, spine['Hook_id_text'] == d_hook['hook_oid'])
    unions.append(agg_by_tag(s_th, d_hook['Hook'], 'Text_Hook'))

    # 7. Text_Promise
    s_tp = spine.join(d_promise, spine['Promise_id_text'] == d_promise['promise_oid'])
    unions.append(agg_by_tag(s_tp, d_promise['Promise'], 'Text_Promise'))

    # 8. Text_Structure (String, no join)
    unions.append(agg_by_tag(spine, spine['Structure'], 'Text_Structure'))

    return ibis.union(*unions).execute()


# -------------------------
# Registry
# -------------------------

TRANSFORMS: Dict[str, TransformSpec] = {
    'weekly_metrics_prod': TransformSpec(
        name='weekly_metrics_prod',
        transform=weekly_metrics_joined_transform,
        input_tables={
            'perf': 'Weekly_runs',
            'ads': 'Ads',
        },
        output_table='Derived_Weekly_Ad_Metrics',
        overwrite=True,
        select_rename={
            'perf': {
                'Week': 'Week',
                'Ad': 'Ad_id',
                'Spend': 'Spend',
                'Leads': 'Leads',
            },
            'ads': {
                'id': 'id',
                'Name': 'Name',
                'Campaign': 'Campaign',
            },
        },
    ),
    'lifetime_ad_metrics_prod': TransformSpec(
        name='lifetime_ad_metrics_prod',
        transform=lifetime_ad_metrics_transform,
        input_tables={
            'perf': 'Weekly_runs',
            'ads': 'Ads',
        },
        output_table='Derived_Lifetime_Ad_Metrics',
        overwrite=True,
        select_rename={
            'perf': {
                'Week': 'Week',
                'Ad': 'Ad_id',
                'Spend': 'Spend',
                'Leads': 'Leads',
            },
            'ads': {
                'id': 'id',
                'Name': 'Name',
                'Campaign': 'Campaign',
            },
        },
    ),
    'tag_lifetime_rollups_prod': TransformSpec(
        name='tag_lifetime_rollups_prod',
        transform=tag_lifetime_rollups_transform,
        input_tables={
            'perf': 'Weekly_runs',
            'ads': 'Ads',
            'creatives': 'Creatives',
            'media': 'Media',
            'headlines': 'Headlines',
            'texts': 'Texts',
            'media_style': 'Media_Style',
            'media_energy': 'Media_Energy',
            'tone': 'Tone',
            'promise_types': 'Promise_types',
            'hook_types': 'Hook_types',
        },
        output_table='Derived_Tag_Lifetime_Rollups',
        overwrite=True,
        select_rename={
            'perf': {
                'Week': 'Week',
                'Ad': 'Ad_id',
                'Spend': 'Spend',
                'Leads': 'Leads',
            },
            'ads': {
                'id': 'ad_oid',
                'Creative': 'Creative_id',
                'Text': 'Text_id',
            },
            'creatives': {
                'id': 'creative_oid',
                'Media': 'Media_id',
                'Headline': 'Headline_id',
            },
            'media': {
                'id': 'media_oid',
                'Media_Style': 'Media_Style_id',
                'Media_Energy': 'Media_Energy_id',
            },
            'headlines': {
                'id': 'headline_oid',
                'Tone': 'Tone_id',
                'Promise': 'Promise_id_headline',
                'Hooks': 'Hooks_id',
            },
            'texts': {
                'id': 'text_oid',
                'Hook': 'Hook_id_text',
                'Promise': 'Promise_id_text',
                'Structure': 'Structure',
            },
            'media_style': {'id': 'style_oid', 'Media_Style': 'Media_Style'},
            'media_energy': {'id': 'energy_oid', 'Media_Energy': 'Media_Energy'},
            'tone': {'id': 'tone_oid', 'Tone': 'Tone'},
            'promise_types': {'id': 'promise_oid', 'Promise': 'Promise'},
            'hook_types': {'id': 'hook_oid', 'Hook': 'Hook'},
        },
    ),
}
