# define salary_processing function
import numpy as np
import re
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity


# define a function to check similarity between jobs based on the title and teaser
def check_similarity(df):
    # try: get job_id, title, teaser for non-null rows, save to df
    try:
        df = df[['job_id', 'title', 'teaser']].dropna()
        # combine title and teaser
        df['title_teaser'] = df['title'] + ' ' + df['teaser']
        # drop the title and teaser columns
        df.drop(['title', 'teaser'], axis=1, inplace=True)
    except:
        raise ValueError('check_similarity: df does not contain job_id, title, teaser columns')

    # define a function to clean the text
    def _clean_text(text):
        # remove non-letters
        letters_only = re.sub("[^a-zA-Z]", " ", text)
        # convert to lower case and split
        words = letters_only.lower().split()
        # download stopwords
        nltk.download('stopwords')
        # remove stop words
        stops = set(stopwords.words("english"))
        meaningful_words = [w for w in words if not w in stops]
        # join the words back into one string separated by space, and return the result.
        return " ".join(meaningful_words)

    # apply the function to title_teaser column
    df['title_teaser'] = df['title_teaser'].apply(_clean_text)

    # vectorize the title_teaser column
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df['title_teaser'])

    # calculate the cosine similarity
    similarity = cosine_similarity(X)

    # cluster the jobs based on the similarity using DBSCAN
    clustering = DBSCAN(eps=0.5, min_samples=2).fit(similarity)

    # add the cluster label to the DataFrame
    df['cluster'] = clustering.labels_

    # for each cluster except -1, get the minimum job_id, store to a dictionary keep_dict
    keep_dict = {}
    for i in df['cluster_n'].unique():
        if i != -1:
            keep_dict[i] = df[df['cluster_n'] == i]['job_id'].min()

    # create a new column similarity_checked, set to True if job_id is in keep_dict.values() or cluster_n is -1, else False
    df['similarity_checked'] = df.apply(
        lambda x: True if x['job_id'] in keep_dict.values() or x['cluster_n'] == -1 else False, axis=1)

    # drop the title_teaser, cluster_n columns
    df.drop(['title_teaser', 'cluster_n'], axis=1, inplace=True)

    # merge the df with the original df, on job_id
    df = df.merge(df, on='job_id', how='left')

    # return the df
    return df


def salary_processing(df):
    # try: get job_id, salary, salary_type for non-null rows, save to salary_df
    try:
        salary_df = df[['job_id', 'salary', 'salary_type']].dropna()
    except:
        raise ValueError('salary_processing: df does not contain job_id, salary, salary_type columns')

    # only keep the rows where salary contains numbers
    salary_df = salary_df[salary_df['salary'].str.contains(r'\d')]

    # define a function to extract salary based on the salary_type, perform as above and convert to list in numeric format
    def _extract_salary(row):
        if row['salary_type'] == 'HourlyRate':
            return [int(i) * 2080 for i in re.findall(r'\d+', row['salary'].split('.')[0])]
        elif row['salary_type'] == 'AnnualPackage':
            return [int(i) * 1000 if int(i) < 300 else int(i) for i in
                    re.findall(r'\d+', row['salary'].replace('$', '').replace(',', ''))]
        else:
            return np.nan

    # apply the function to salary_df
    salary_df['extract_salary'] = salary_df.apply(_extract_salary, axis=1)

    # for each row in extract_salary column, drop the values <30000 in the list
    salary_df['extract_salary'] = salary_df['extract_salary'].apply(lambda x: [i for i in x if i >= 30000])

    # drop the rows where extract_salary is empty
    salary_df = salary_df[salary_df['extract_salary'].apply(lambda x: len(x) > 0)]

    # set salary lower bound, upper bound, mid point
    salary_df['salary_lower_bound'] = salary_df['extract_salary'].apply(lambda x: min(x))
    salary_df['salary_upper_bound'] = salary_df['extract_salary'].apply(lambda x: max(x))
    salary_df['salary_mid_point'] = salary_df['extract_salary'].apply(lambda x: np.mean(x))

    # drop the extract_salary column
    salary_df.drop(columns=['extract_salary'], inplace=True)

    # merge the salary_df with the original df
    df = df.merge(salary_df, how='left', on='job_id')

    # return the df
    return df
