"""Top-level package for au-nz-jobs."""

__author__ = """Robert Tu"""
__email__ = 'tsy0716@gmail.com'
__version__ = '0.1.2'

# imports
from au_nz_jobs.downloader import Job, Jobs
from au_nz_jobs.save_jobs import save_jobs, save_jobs_sqlite
