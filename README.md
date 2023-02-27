# au-nz-jobs

[![image](https://img.shields.io/pypi/v/au_nz_jobs.svg)](https://pypi.python.org/pypi/au_nz_jobs)

[![image](https://img.shields.io/travis/tsy0716/au_nz_jobs.svg)](https://travis-ci.com/tsy0716/au_nz_jobs)

[![Documentation Status](https://readthedocs.org/projects/au-nz-jobs/badge/?version=latest)](https://au-nz-jobs.readthedocs.io/en/latest/?version=latest)

A package to download and save jobs in Australian and New Zealand from
SEEK.

## About
I am a data scientist based in AU/NZ. I found it quite overwhelming to search jobs from SEEK.
It needs lots of clicks and time to find the right jobs. Going deeper, if you want to have a better understanding of the
trends of the job market, there isn't a handy tool to download the jobs and do some analysis.

This package is to help job seekers/HR guys/companies to batch download jobs from SEEK and save them to local files.

It also provides some basic analysis and visualization tools to help you understand the job market better (roadmap).

## Development Status
This package is still in early development stage. Use it at your own risk.

## Features

### downloader
Sub package to download jobs from SEEK.

- Search jobs by:
  - multiple keywords in batch
  - multiple locations in batch
  - date range: last n days
  - job type: full-time, part-time, contract, casual
  - sort mode: relevance, date
- The default search in SEEK will yield too many results(including ads and unrelated jobs)
  - You can define a check_words list to filter out the irrelevant jobs
- The job details will be further downloaded based on the filtered job

- Output, a dictionary of DataFrames as below:
  - jobs_wide: a wide formatted DataFrame with one row per job including all downloaded job details.
    - If you want to get a single table containing all the information, this is the one.

  - jobs: similar to jobs_wide, but only the dimension_id columns are kept.
    - This is for those who will work on the jobs data for a relational database. Need to work with other dimension tables.

  - dimension tables:
    - classification: SEEK job classification, generally the industry, e.g. Construction, Engineering, Information & Communication Technology
    - sub_classification: SEEK job sub-classification, more specific than classification, NO father-child relationship to classification
    e.g. Water & Waste Engineering, Programme & Project Management
    - location: high-level location, e.g. Sydney, Melbourne, Brisbane
    - area: more specific location, e.g. Sydney CBD, Inner West
    - advertiser: the advertiser of the job, can be different from the actual company
    - company_review: only for the jobs which have company reviews

### save_jobs
Sub package to save the downloaded jobs to local files.

- save the downloaded jobs from downloaded DataFrames to local files
- choose from single table(jobs_wide) or relational database tables (jobs and dimension tables)
- output as csv, excel, sqlite
  - csv: one csv file per table
  - excel: a single excel file with single sheet for single table, multiple sheets for relational database tables
  - sqlite: a single sqlite file with multiple tables (coming soon)

- Sqlite is required for further analysis and visualization modules. (coming soon)
- NO other SQL databases will be supported. Please handle the data by yourself.

### analysis (roadmap)

### visualization (roadmap)

## Installation

```shell
pip install au-nz-jobs
```
## NOTE for downloader!
**Please CAREFULLY read the following limitations before using this package.**

## Implicit Steps for downloader
1. For each keyword and location pair in given date range,the jobs without details will be downloaded first.
2. The downloaded jobs from step 1 will be then filtered by the check_words list.
3. Further details of jobs in step 2 will be downloaded.
4. Jobs data from step 3 will cleaned and restructured to DataFrames.

## Limitations
- This package is based on the api provided by SEEK.
- The api is not officially supported by SEEK. Any changes to the api will break this package.
- This package is **ONLY** for **PERSONAL USE**. Please do not use it for any commercial purpose.
- Downloading jobs takes might take a long time. Please be patient.
- Some suggestions to save you some time:
  - reduce keywords and locations, each pair of keyword and location will be iterated through
    - e.g. A download with 3 keywords and 3 locations will yield 9 searches!!!
  - reduce the date range, 31 days is the maximum, and it can take a long time to download
  - limit the location to city rather than state or country (you can search by state or country anyway)
    - e.g. Sydney rather than NSW or Australia
- For a single keyword and location pair, no matter of the date range, the maximum number of jobs you can download is 550.

## Usage

```python
from au_nz_jobs import Jobs,save_jobs

# define the keywords you want to search in a list
keywords = ['data scientist', 'data engineer']

# define the locations you want to search in a list
locations = ['Sydney', 'Melbourne']

# The default download will yield too many results(including ads and unrelated jobs)
# A check_words list is STRONGLY recommended to filter out the irrelevant jobs
# The check_words list should contain the most related words to the job you want to search
check_words = ['data', 'scientist']

# define the date_range for jobs to be downloaded, 3 means last 3 days
date_range = 3

# initiate the Jobs class
# parameters:
#   keywords: a list of keywords to search
#   locations: a list of locations to search
#   work_type: a list of work types to search, options: ['full-time', 'part-time', 'contract', 'casual'], all by default
data_jobs = Jobs(keywords, locations, work_type=['full-time', 'part-time', 'contract', 'casual'])

# download all dfs
# parameters:
#   date_range: the date range to search, 3 means last 3 days
#   check_words: a list of words to filter out the irrelevant jobs
#   sort_mode: the sort mode for the search, options: ['relevance', 'date'], date by default
df_dict = data_jobs.get_all_dfs(date_range,check_words=check_words)

# save the downloaded jobs to local files
# parameters:
#   format: csv, excel
#   single_table: True for single table, False for relational database tables
#   path: the path to save the files
#   NO need to specify the file name, the file name will be generated automatically
#   jobs.csv, jobs.xlsx, jobs.db for single table
#   [jobs,classification,sub_classification,location,area,advertiser,company_review].csv for relational database tables
save_jobs(df_dict,format='csv',single_table=True,path='data')

```

## Roadmap
- [x] downloader
- [x] save_jobs: csv, excel
- [ ] save_jobs: sqlite
- [ ] add documentation to readthedocs
- [ ] add tests
- [ ] tableau public dashboard of data related jobs based on this package
- [ ] analysis and visualization - will break down to smaller tasks


## Contributing

If you have any questions or suggestions, please feel free to open an issue or pull request.
Other developers are welcome to contribute to this project. Feel free to mail me if you have any questions.
Email: tsy0716@gmail.com

## License
GPL-3.0

## Credits

Credit to [job-seeker](https://github.com/PyBites-Open-Source/job-seeker) for the idea.

Credit to [seek/au](https://www.seek.com.au/) and [seek/nz](https://www.seek.co.nz/) for the api.

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.
