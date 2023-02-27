import requests
import json
import pandas as pd
import numpy as np
import re
import time


# naming convention:
# variables and fields in df and database: snake_case


# define the Job class: detailed information of a certain job
class Job:
    SEEK_API_URL = "https://www.seek.com.au/api/chalice-search/search"
    SEEK_API_URL_JOB = "https://chalice-experience-api.cloud.seek.com.au/job"

    def __init__(self, job_id: str):
        """
        :param job_id: job id
        """
        self.job_id = job_id

    # define a function to download the job information
    def download(self):
        # initiate the url
        url = f"{self.SEEK_API_URL_JOB}/{self.job_id}"

        # api request
        r = requests.get(url=url)

        # convert to json
        r = r.json()

        # get expiryDate,salaryType,hasRoleRequirements,roleRequirements,jobAdDetails,contactMatches, use.get() to
        # avoid key error
        expiry_date = r.get("expiryDate")
        salary_type = r.get("salaryType")
        has_role_requirements = r.get("hasRoleRequirements")
        role_requirements = r.get("roleRequirements")
        job_ad_details = r.get("jobAdDetails")
        contact_matches = r.get("contactMatches")

        # define the function to get the email and phone number from a single contact
        def get_contact(contact):
            contact_dict = {'Email': [], 'Phone': []}
            for j in range(len(contact)):
                if contact[j]['type'] == 'Email':
                    contact_dict['Email'].append(contact[j]['value'])
                elif contact[j]['type'] == 'Phone':
                    contact_dict['Phone'].append(contact[j]['value'])
            # define the regex for email
            email_regex = re.compile(r'[\w\.-]+@[\w\.-]+')
            # loop through the email list
            for j in range(len(contact_dict['Email'])):
                # trim the space
                contact_dict['Email'][j] = contact_dict['Email'][j].replace(' ', '')
                # remove the nbsp
                contact_dict['Email'][j] = contact_dict['Email'][j].replace('&nbsp;', '')
                # get the email
                contact_dict['Email'][j] = email_regex.findall(contact_dict['Email'][j])[0]
                # trim all non number and letter characters in the beginning and end
                contact_dict['Email'][j] = contact_dict['Email'][j].strip('!@#$%^&*()_+-=,./<>?;:\'"[]{}\\|`~')
                # remove the special characters
                contact_dict['Email'][j] = ''.join(
                    [x for x in contact_dict['Email'][j] if x.isalnum() or x in ['@', '.', '_', '-']])
            # loop through the phone list to trim all the space and only keep the numbers and +
            for j in range(len(contact_dict['Phone'])):
                contact_dict['Phone'][j] = contact_dict['Phone'][j].replace(' ', '')
                contact_dict['Phone'][j] = ''.join([x for x in contact_dict['Phone'][j] if x.isalnum() or x in ['+']])
            # replace [] with None
            if not contact_dict['Email']:
                contact_dict['Email'] = None
            if not contact_dict['Phone']:
                contact_dict['Phone'] = None

            return contact_dict

        # get the contact from contact_matches
        email = get_contact(contact_matches)['Email']
        phone = get_contact(contact_matches)['Phone']

        # get companyOverallRating,companyProfileUrl,companyName,companyId under companyReview
        # check for companyReview, if not exist, set to None
        if r.get("companyReview") is None:
            company_overall_rating = None
            company_profile_url = None
            company_name_review = None
            company_id = None
        else:
            company_overall_rating = r.get("companyReview").get("companyOverallRating")
            company_profile_url = r.get("companyReview").get("companyProfileUrl")
            company_name_review = r.get("companyReview").get("companyName")
            company_id = r.get("companyReview").get("companyId")

        # build a dictionary including job_id and all the information above
        job_details = {"id": self.job_id, "expiry_date": expiry_date, "salary_type": salary_type,
                       "has_role_requirements": has_role_requirements, "role_requirements": role_requirements,
                       "job_ad_details": job_ad_details, "email": email, "phone": phone,
                       "company_overall_rating": company_overall_rating, "company_profile_url": company_profile_url,
                       "company_name_review": company_name_review, "company_id": company_id}

        # write to attribute
        self.job_details = job_details

        # return the dictionary
        return job_details


# define Jobs class: basic information of the jobs to search
class Jobs:
    SEEK_API_URL = "https://www.seek.com.au/api/chalice-search/search"
    SEEK_API_URL_JOB = "https://chalice-experience-api.cloud.seek.com.au/job"

    def __init__(self, keywords: list, locations: list, work_type: list = None, check_words: list = None):
        """
        :param keywords: list of keywords to search
        :param locations: list of locations to search
        :param work_type: list of work type to search, default to None which means all work types
            options: ['full_time', 'part_time', 'contract', 'casual']
        """
        self.keywords = keywords
        self.locations = locations
        self.work_type = work_type
        self.check_words = check_words
        self.if_downloaded = False
        self.if_download_details = False

        # work_type id dictionary
        self.work_type_dict = {
            'full_time': 242,
            'part_time': 243,
            'contract': 244,
            'casual': 245
        }

        options = ['full_time', 'part_time', 'contract', 'casual']
        # check if the work_type is valid and convert work_type to work_type_id
        if self.work_type is not None:
            for i in self.work_type:
                if i not in options:
                    raise ValueError(f"Invalid work_type: {i}, please choose from {options}")
            self.work_type_id = [self.work_type_dict[i] for i in self.work_type]

        else:
            self.work_type_id = self.work_type_dict.values()

    def download(self, date_range: int = 31, sort_mode: str = 'date'):
        """
        :param date_range: number of days back from today to search, default to 31
        :param sort_mode: sort mode, default to 'date'
            options: ['relevance', 'date']
        :return: a list of jobs
        """

        # convert sort_mode
        sort_mode_dict = {
            'relevance': 'KeywordRelevance',
            'date': 'ListedDate'
        }
        # check if the sort_mode is valid
        if sort_mode not in sort_mode_dict.keys():
            raise ValueError(f"Invalid sort_mode: {sort_mode}, please choose from {sort_mode_dict.keys()}")
        sort_mode = sort_mode_dict[sort_mode]

        # define a function to download for a single pair of keyword and location
        def _download_jobs(keyword, location):
            # start timer
            start_time = time.time()

            # initiate the parameters
            params = dict(
                siteKey="AU-Main",
                sourcesystem="houston",
                page="1",
                seekSelectAllPages="true",
                sortmode=sort_mode,
                dateRange=date_range,
                # unpack the work_type_id and join with comma
                worktype=','.join([str(i) for i in self.work_type_id]),
                keywords=keyword,
                where=location
            )

            # api request
            resp = requests.get(url=self.SEEK_API_URL, params=params)

            # convert the response to json
            json_resp = resp.json()

            # get the total number job count
            total_job_count = json_resp.get('totalCount')

            # if total_job_count is 0, return empty list
            if total_job_count == 0:
                print(f"No jobs found for keyword: {keyword}, location: {location} in the last {date_range} days.")
                print("You can try again with longer date range or different keywords/location.")
                return []

            # convert job count to number of pages
            if total_job_count % 20 == 0:
                pages = total_job_count // 20
            else:
                pages = total_job_count // 20 + 1

            # initiate the jobs list
            jobs = []

            # loop through the pages
            for page in range(1, pages + 1):
                # update the page number
                params['page'] = page
                # api request
                resp = requests.get(url=self.SEEK_API_URL, params=params)
                # convert the response to json
                json_resp = resp.json()
                # get the jobs
                jobs += json_resp.get('data')

            # end timer
            end_time = time.time()
            print(
                f"Downloaded {len(jobs)} jobs for keyword: {keyword}, location: {location} in {(end_time - start_time):.2f} seconds.")

            # return the jobs
            return jobs

        # initiate the jobs list
        jobs = []

        # loop through the keywords and locations
        for keyword in self.keywords:
            for location in self.locations:
                # download the jobs
                jobs += _download_jobs(keyword, location)

        # check if the jobs is empty, if yes, return empty dataframe, write if_downloaded to True
        if len(jobs) == 0:
            print("No jobs found for all keyword/location combination in given date_range.")
            print("Please try again with different keywords/locations/date_range.")
            self.if_downloaded = True
            return pd.DataFrame()

        # convert the jobs to dataframe
        jobs = pd.DataFrame(jobs)

        # define a function to clean the jobs dataframe
        def _clean_jobs(df):
            # drop the duplicate jobs based on id
            df.drop_duplicates(subset=['id'], inplace=True)

            # drop the unnecessary columns: logo, isStandOut, automaticInclusion, displayType, templateFileName,
            # tracking, solMetadata, branding, categories
            df.drop(
                columns=['logo', 'isStandOut', 'automaticInclusion', 'displayType', 'templateFileName', 'tracking',
                         'solMetadata', 'branding', 'categories'], inplace=True)

            # drop the columns with names in numbers
            df.drop(columns=[i for i in df.columns if i.isdigit()], inplace=True)

            # rename all camel case columns to snake case
            df.rename(columns={i: re.sub(r'(?<!^)(?=[A-Z])', '_', i).lower() for i in df.columns}, inplace=True)

            # convert area_id, suburb_id to Int64
            df['area_id'] = df['area_id'].astype('Int64')
            df['suburb_id'] = df['suburb_id'].astype('Int64')

            # split the advertiser column, example: {'description': 'Seek Limited', 'id': '20242373'}
            df['advertiser_title'] = df['advertiser'].apply(lambda x: x['description'])
            df['advertiser_id'] = df['advertiser'].apply(lambda x: x['id'])
            df.drop(columns=['advertiser'], inplace=True)
            # rename the advertiser_title column to advertiser
            df.rename(columns={'advertiser_title': 'advertiser'}, inplace=True)

            # split the classification column, example: { 'id': '6304', 'description': 'Information & Communication
            # Technology'}
            df['classification_title'] = df['classification'].apply(lambda x: x['description'])
            df['classification_id'] = df['classification'].apply(lambda x: x['id'])
            df.drop(columns=['classification'], inplace=True)
            # rename the classification_title column to classification
            df.rename(columns={'classification_title': 'classification'}, inplace=True)

            # split the sub_classification column, example: {'id': '6311', 'description': 'Database Development'}
            df['sub_classification_title'] = df['sub_classification'].apply(lambda x: x['description'])
            df['sub_classification_id'] = df['sub_classification'].apply(lambda x: x['id'])
            df.drop(columns=['sub_classification'], inplace=True)
            # rename the sub_classification_title column to sub_classification
            df.rename(columns={'sub_classification_title': 'sub_classification'}, inplace=True)

            # return the jobs dataframe
            return df

        # clean the jobs dataframe
        jobs = _clean_jobs(jobs)

        # write to attribute
        self.jobs_df = jobs
        self.if_downloaded = True

        print(f"After cleaning, download {len(jobs)} jobs in total.")

        # return the jobs dataframe
        return jobs

    # define a function to get classification_df
    def _classification_df(self):
        """
        :return: a dataframe of classification
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")

        # get the classification dataframe
        classification_df = self.jobs_df[['classification', 'classification_id']].drop_duplicates()
        # reset the index
        classification_df.reset_index(drop=True, inplace=True)

        # drop null rows
        classification_df.dropna(inplace=True)

        # write to attribute
        self.classification_df = classification_df

        # return the classification dataframe
        return classification_df

    # define a function to get sub_classification_df
    def _sub_classification_df(self):
        """
        :return: a dataframe of sub_classification
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # get the sub_classification dataframe
        sub_classification_df = self.jobs_df[['sub_classification', 'sub_classification_id']].drop_duplicates()
        # reset the index
        sub_classification_df.reset_index(drop=True, inplace=True)

        # drop null rows
        sub_classification_df.dropna(inplace=True)

        # write to attribute
        self.sub_classification_df = sub_classification_df

        # return the sub_classification dataframe
        return sub_classification_df

    # define a function to get location_df
    def _location_df(self):
        """
        :return: a dataframe of location
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # get the location dataframe
        location_df = self.jobs_df[['location', 'location_id']].drop_duplicates()
        # reset the index
        location_df.reset_index(drop=True)

        # drop null rows
        location_df.dropna(inplace=True, how='all')

        # write to attribute
        self.location_df = location_df

        # return the location dataframe
        return location_df

    # define a function to get area_df
    def _area_df(self):
        """
        :return: a dataframe of area
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # get the area dataframe
        area_df = self.jobs_df[['area', 'area_id']].drop_duplicates()
        # reset the index
        area_df.reset_index(drop=True, inplace=True)

        # drop null rows
        area_df.dropna(inplace=True)

        # write to attribute
        self.area_df = area_df

        # return the area dataframe
        return area_df

    # define a function to get the advertiser_df
    def _advertiser_df(self):
        """
        :return: a dataframe of advertiser
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # get the advertiser dataframe
        advertiser_df = self.jobs_df[['advertiser', 'advertiser_id']].drop_duplicates()
        # reset the index
        advertiser_df.reset_index(drop=True, inplace=True)

        # drop null rows
        advertiser_df.dropna(inplace=True)

        # write to attribute
        self.advertiser_df = advertiser_df

        # return the advertiser dataframe
        return advertiser_df

    # define a function to get the cleaned jobs dataframe
    def _jobs_cleaned_df(self):
        """
        :return: a dataframe of jobs
        """
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # copy the jobs dataframe
        jobs_cleaned_df = self.jobs_df.copy()

        # drop the unnecessary columns: classification, sub_classification, location, area, suburb_id, advertiser,
        # locationWhereValue, areaWhereValue, suburbWhereValue
        jobs_cleaned_df.drop(
            columns=['classification', 'sub_classification', 'location', 'area', 'advertiser', 'location_where_value',
                     'area_where_value', 'suburb_where_value'], inplace=True)

        # drop null rows
        jobs_cleaned_df.dropna(inplace=True, how='all')

        # write to attribute
        self.jobs_cleaned_df = jobs_cleaned_df

        # return the jobs_cleaned_df
        return jobs_cleaned_df

    # define a function to do check_words
    def _check_words(self, jobs, check_words):
        # check for if check_words is None, if so, return the jobs dataframe
        if check_words is None:
            return jobs

        # print the row number of jobs dataframe
        print(f"Before checking words, there are {len(jobs)} jobs in total.")

        # extract check_words from teaser, create a new column called "check_words_found_teaser", each keyword
        # should be a single word, ignore case
        import re
        jobs["check_words_found_teaser"] = jobs.teaser.apply(
            lambda x: re.findall(r"\b(" + "|".join(check_words) + r")\b", x, flags=re.IGNORECASE))
        # similar to title
        jobs["check_words_found_title"] = jobs.title.apply(
            lambda x: re.findall(r"\b(" + "|".join(check_words) + r")\b", x, flags=re.IGNORECASE))
        # create a new column called "check_words_found", which is the combination of "check_words_found_teaser"
        # and "check_words_found_title"
        jobs["check_words_found"] = jobs["check_words_found_teaser"] + jobs["check_words_found_title"]
        # lower the words in "check_words_found"
        jobs["check_words_found"] = jobs["check_words_found"].apply(lambda x: [i.lower() for i in x])
        # eliminate the duplicated value in check_words_found
        jobs["check_words_found"] = jobs["check_words_found"].apply(lambda x: list(set(x)))
        # create a new column called "check_words_count", which is the length of "check_words_found"
        jobs["check_words_count"] = jobs["check_words_found"].apply(lambda x: len(x))
        # create a new column called "check_words_checked", which is True if "check_words_count" > 1, otherwise
        # False
        jobs["check_words_checked"] = jobs["check_words_count"].apply(lambda x: True if x > 0 else False)

        # drop the unnecessary columns: check_words_found_teaser, check_words_found_title, check_words_count
        jobs.drop(columns=["check_words_found_teaser", "check_words_found_title", "check_words_count"], inplace=True)

        # print the row number which check_words_checked is True
        print(f"After checking, there are {len(jobs[jobs.check_words_checked])} jobs with check words.")

        # return the jobs dataframe
        return jobs

    # define a function to download job details
    def _download_details(self, check_words=None):
        # check if the jobs_df is downloaded
        if not self.if_downloaded:
            raise ValueError("Please download the jobs_df first")
        # clean the jobs_df
        jobs_cleaned_df = self._jobs_cleaned_df()

        # initialize a list to store the jobs_to_download
        jobs_to_download = []
        # if check_words is None, jobs_to_download is the id column of jobs_cleaned_df
        if check_words is None:
            jobs_to_download = jobs_cleaned_df.id.tolist()
        # if check_words is not None, call the _check_words function
        else:
            jobs_checked_df = self._check_words(jobs_cleaned_df, check_words)
            # the jobs_to_download is the id column of jobs_checked_df where check_words_checked is True
            jobs_to_download = jobs_checked_df[jobs_checked_df.check_words_checked].id.tolist()

        # check if the jobs_to_download is empty, print the message and return jobs_cleaned_df
        # write to attribute: n_jobs_details_downloaded with 0
        if len(jobs_to_download) == 0:
            print("There is no job to download the details.")
            self.n_jobs_details_downloaded = 0
            return jobs_cleaned_df

        # start timer
        start_time = time.time()

        # initialize a list to store the jobs_details
        jobs_details = []

        # loop through the jobs_to_download, create Job class for each job, and download the job details
        for job_id in jobs_to_download:
            job = Job(job_id=job_id)
            job.download()
            jobs_details.append(job.job_details)

        # convert the jobs_details to a dataframe
        jobs_details_df = pd.DataFrame(jobs_details)

        # left join the job_cleaned_df and jobs_details_df on id
        jobs_details_df = jobs_cleaned_df.merge(jobs_details_df, on="id", how="left")

        # write to attribute
        self.jobs_details_df = jobs_details_df
        self.n_jobs_details_downloaded = len(jobs_details_df)

        # print the time taken
        print(f"Job details download finished, time taken: {(time.time() - start_time):.2f} seconds")

        # return the jobs_details_df
        return jobs_details_df

    # define a function to get the company dataframe
    def _company_review_df(self):
        # check if the n_jobs_details_downloaded is 0, if yes, return blank dataframe
        if self.n_jobs_details_downloaded == 0:
            return pd.DataFrame()

        # get the jobs_details_df
        jobs_details_df = self.jobs_details_df

        # get the company_review_df: company_overall_rating, company_profile_url,
        # company_name_review, company_id
        company_review_df = jobs_details_df[["company_overall_rating", "company_profile_url",
                                             "company_name_review", "company_id"]].copy()

        # drop the duplicated rows and the null rows based on company_id
        company_review_df.drop_duplicates(subset="company_id", inplace=True)
        company_review_df.dropna(subset=["company_id"], inplace=True)

        # write to attribute
        self.company_review_df = company_review_df

        # return the company_review_df
        return company_review_df

    # define a function to get all the dataframes
    def get_all_dfs(self, date_range=31, sort_mode='date', check_words=None, if_download_details=True):
        """
        :return: dataframes of jobs, classification, sub_classification, location, area, advertiser, jobs_cleaned
        """

        # if not downloaded, get the jobs dataframe
        if not self.if_downloaded:
            jobs = self.download(date_range=date_range, sort_mode=sort_mode)

        # check if the jobs_cleaned_df is empty, if yes, return
        if len(self._jobs_cleaned_df()) == 0:
            return

        # get the classification dataframe
        classification_df = self._classification_df()

        # get the sub_classification dataframe
        sub_classification_df = self._sub_classification_df()

        # get the location dataframe
        location_df = self._location_df()

        # get the area dataframe
        area_df = self._area_df()

        # get the advertiser dataframe
        advertiser_df = self._advertiser_df()

        # get the cleaned jobs dataframe
        jobs_cleaned_df = self._jobs_cleaned_df()

        # if if_download_details is True, download the job details
        if if_download_details:
            # get the jobs_details dataframe
            jobs_details_df = self._download_details(check_words=check_words)
            # set jobs to jobs_details_df
            jobs = jobs_details_df
        else:
            jobs = jobs_cleaned_df

        # get the company_review dataframe
        company_review_df = self._company_review_df()

        # final cleaning for jobs dataframe
        # remove the company_overall_rating, company_profile_url, company_name_review columns if found in jobs
        if "company_overall_rating" in jobs.columns:
            jobs.drop(columns=["company_overall_rating", "company_profile_url", "company_name_review"], inplace=True)

        # listing_date, expiry_date to datetime
        jobs.listing_date = pd.to_datetime(jobs.listing_date)
        jobs.expiry_date = pd.to_datetime(jobs.expiry_date)

        # has_role_requirements to boolean
        jobs.has_role_requirements = jobs.has_role_requirements.astype(bool)

        # advertiser_id, classification_id, sub_classification_id to int
        jobs.advertiser_id = jobs.advertiser_id.astype(int)
        jobs.classification_id = jobs.classification_id.astype(int)
        jobs.sub_classification_id = jobs.sub_classification_id.astype(int)

        # rename company_id to review_company_id
        jobs.rename(columns={"company_id": "review_company_id"}, inplace=True)

        # rename id to job_id
        jobs.rename(columns={"id": "job_id"}, inplace=True)

        # replacing all null values to np.nan: '[]', '{}', None, blank string,[],{}
        jobs.replace({'[]': np.nan, '{}': np.nan, '': np.nan, None: np.nan}, inplace=True)

        # for company_review_df, rename company_id to review_company_id
        if len(company_review_df) > 0:
            company_review_df.rename(columns={"company_id": "review_company_id"}, inplace=True)

        # for other dfs other than jobs, change the type of xxx_id to the same as jobs, take care of the Int64
        classification_df.classification_id = classification_df.classification_id.astype(int)
        sub_classification_df.sub_classification_id = sub_classification_df.sub_classification_id.astype(int)
        location_df.location_id = location_df.location_id.astype(int)
        area_df.area_id = area_df.area_id.astype('Int64')
        advertiser_df.advertiser_id = advertiser_df.advertiser_id.astype(int)

        # join all dfs to a single df jobs_wide
        jobs_wide = jobs.merge(classification_df, on="classification_id", how="left")
        jobs_wide = jobs_wide.merge(sub_classification_df, on="sub_classification_id", how="left")
        jobs_wide = jobs_wide.merge(location_df, on="location_id", how="left")
        jobs_wide = jobs_wide.merge(area_df, on="area_id", how="left")
        jobs_wide = jobs_wide.merge(advertiser_df, on="advertiser_id", how="left")
        # if company_review_df is not empty, join it to jobs_wide
        if len(company_review_df) > 0:
            jobs_wide = jobs_wide.merge(company_review_df, on="review_company_id", how="left")

        # generate the dataframes dictionary
        df_dict = {'classification': classification_df, 'sub_classification': sub_classification_df,
                   'location': location_df, 'area': area_df, 'advertiser': advertiser_df,
                   'jobs': jobs, 'company_review': company_review_df, 'jobs_wide': jobs_wide}

        # return the dataframes dictionary
        return df_dict


# test the Jobs class
if __name__ == '__main__':
    # define the search keywords list
    keywords_list = ['data analyst']
    # define the search location list
    locations_list = ['All New Zealand']
    # define the date range
    date_range = 3
    # define the check words
    check_words = ["data", "analyst", "science", "engineer", "engineering", "scientist", "analytics",
                   "business intelligence", "business intelligence", "business analyst", "power bi", "powerbi",
                   "power-bi", "tableau", "python", "R", "machine learning", "ai",
                   "artificial intelligence", "BI"]

    # initiate the job class
    data_jobs = Jobs(keywords_list, locations_list)

    # get all the dataframes
    df_dict = data_jobs.get_all_dfs(date_range=date_range, check_words=check_words, if_download_details=True)
