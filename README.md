# AI Weekly Data Analyst — FastAPI Backend

A production-ready FastAPI service that accepts an Excel file and a date range,
groups the data into weekly buckets, and returns AI-generated performance
summaries powered by **Google Gemini**.

---

## Project Structure

```
ai_weekly_analyst/
├── main.py                    # FastAPI app entry point
├── requirements.txt
├── .env.example               # Copy to .env and fill in your keys
│
├── core/
│   ├── config.py              # Pydantic BaseSettings (reads .env)
│   └── exceptions.py          # Custom exception classes
│
├── schemas/
│   └── analysis.py            # Pydantic request / response models
│
├── services/
│   ├── data_processor.py      # Pandas: parse → filter → resample
│   └── ai_service.py          # Gemini API integration
│
├── routers/
│   └── analysis.py            # POST /api/v1/analyze endpoint
│
└── tests/
    └── test_data_processor.py # Pytest unit tests
```

---

## Quick Start

### 1. Clone & install dependencies

```bash
git clone <repo-url>
cd ai_weekly_analyst
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
```

### 3. Run the server

```bash
uvicorn ai_weekly_analyst.main:app --reload --port 8000
```

Interactive API docs → **http://localhost:8000/docs**

---

## API Usage

### `POST /api/v1/analyze`

| Field        | Type          | Description                              |
|--------------|---------------|------------------------------------------|
| `file`       | `.xlsx` file  | Excel file with a `Date` column          |
| `start_date` | `string`      | ISO date, e.g. `2024-07-01`              |
| `end_date`   | `string`      | ISO date, e.g. `2024-07-31`              |

#### cURL example

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@sales_data.xlsx" \
  -F "start_date=2024-07-01" \
  -F "end_date=2024-07-31"
```

#### Python example (httpx)

```python
import httpx

with open("sales_data.xlsx", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/api/v1/analyze",
        files={"file": ("sales_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"start_date": "2024-07-01", "end_date": "2024-07-31"},
    )

print(response.json())
```

#### Sample response

```json
{
  "status": "success",
  "file_name": "sales_data.xlsx",
  "start_date": "2024-07-01",
  "end_date": "2024-07-31",
  "total_weeks_analyzed": 4,
  "weekly_results": [
    {
      "week_ending": "2024-07-07",
      "stats": {
        "week_ending": "2024-07-07",
        "metrics": {
          "Sales_sum": 721.0,
          "Sales_mean": 103.0,
          "Units_sum": 91.0,
          "Units_mean": 13.0
        }
      },
      "ai_summary": "Week ending July 7 showed solid early-month momentum with 721 total sales across 7 days.",
      "peak_day": "2024-07-05 (Friday)",
      "trend_vs_previous_week": "No previous week data available."
    }
  ]
}
```

---

## Excel File Format

Your `.xlsx` file must contain a `Date` column (configurable via `DATE_COLUMN_NAME`
env var). All other numeric columns are aggregated automatically.

| Date       | Sales | Units | Revenue |
|------------|-------|-------|---------|
| 2024-07-01 | 120   | 15    | 1800    |
| 2024-07-02 | 98    | 12    | 1470    |
| ...        | ...   | ...   | ...     |

---

## Error Handling

| Scenario               | HTTP Code | `error_type`         |
|------------------------|-----------|----------------------|
| Non-.xlsx file         | 400       | `InvalidFileFormat`  |
| Missing `Date` column  | 422       | `MissingDateColumn`  |
| No data in date range  | 422       | `EmptyDateRange`     |
| Invalid date format    | 400       | *(detail string)*    |
| AI service failure     | Soft-fail | Summary placeholder  |

AI errors are handled gracefully — the endpoint still returns raw stats with
a placeholder message if Gemini is unreachable or misconfigured.

---

## Running Tests

```bash
pytest ai_weekly_analyst/tests/ -v
```

---

## Configuration Reference

| Variable          | Default               | Description                    |
|-------------------|-----------------------|--------------------------------|
| `GEMINI_API_KEY`  | *(required)*          | Google Gemini API key          |
| `GEMINI_MODEL`    | `gemini-1.5-flash`    | Model name                     |
| `MAX_FILE_SIZE_MB`| `10`                  | Upload size limit (MB)         |
| `DATE_COLUMN_NAME`| `Date`                | Expected date column header    |
