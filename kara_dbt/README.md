# kara_dbt

Transforms the operational tables in `raw.*` (written by
`app.scraper.load_raw_to_pg` and `kara_detection.detect_images`) into the
`analytics` schema the API and reports read from.

## Layers

- **staging** (`models/staging`, view-materialized): 1:1 cleaning of
  `raw.telegram_messages` -- normalizes fields and mints `message_key`, a
  surrogate key over `(channel, message_id)` since Telegram message ids are
  only unique per channel.
- **marts** (`models/marts`, table-materialized):
  - `dim_channels`, `dim_dates` -- dimensions
  - `fct_messages` -- one row per message
  - `fct_message_products` -- message-to-product/drug bridge table, built
    by keyword-matching message text against `seeds/product_dictionary.csv`
  - `fct_image_detections` -- reads `raw.image_detections` (written by
    `kara_detection.detect_images`) and resolves it to `message_id`

## Running

```bash
cp profiles.yml.example profiles.yml   # fill in nothing -- it reads env vars
export DBT_PROFILES_DIR=.              # from inside kara_dbt/
dbt deps
dbt seed
dbt run
dbt test
```

Or from the repo root: `dbt run --project-dir kara_dbt --profiles-dir kara_dbt`.

## Adding a new tracked product/drug

Add a row to `seeds/product_dictionary.csv` (`product_name,keyword,category`)
and re-run `dbt seed && dbt run`. No code change needed -- this is what
backs `/api/reports/top-products`.
