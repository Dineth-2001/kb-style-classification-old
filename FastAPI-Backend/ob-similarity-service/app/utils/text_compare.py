from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from Levenshtein import distance as levenshtein_distance
from fuzzywuzzy import fuzz
from app.utils.data_transform import (
    get_operation_machine_list,
    get_operation_machine_list_db,
)
import concurrent.futures


def preprocess_text(text):
    preprocessed_text = text.lower().strip()
    preprocessed_text = " ".join(word.strip() for word in preprocessed_text.split())
    return preprocessed_text


# Levenshtein Distance (Normalized)
def normalized_levenshtein(str1, str2):
    return 1 - (levenshtein_distance(str1, str2) / max(len(str1), len(str2)))


# Jaccard Similarity
def jaccard_similarity(str1, str2):
    set1, set2 = set(str1.split()), set(str2.split())
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


# Levenshtein Distance (Normalized)
def normalized_levenshtein(str1, str2):
    return 1 - (levenshtein_distance(str1, str2) / max(len(str1), len(str2)))


# Cosine Similarity with TF-IDF
def cosine_similarity_tfidf(str1, str2):
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform([str1, str2])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return cosine_sim[0][0]


# fuzz similarity
def fuzz_similarity(str1, str2):
    simple_ratio = fuzz.ratio(str1, str2)
    partial_ratio = fuzz.partial_ratio(str1, str2)
    token_sort_ratio = fuzz.token_sort_ratio(str1, str2)
    token_set_ratio = fuzz.token_set_ratio(str1, str2)
    wratio = fuzz.WRatio(str1, str2)

    avg_score = np.mean(
        [simple_ratio, partial_ratio, token_sort_ratio, token_set_ratio, wratio]
    )
    # avg_score = np.mean([token_set_ratio, wratio])
    return avg_score


def get_similarity_score(text1, text2):
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    # jaccard_sim = jaccard_similarity(text1, text2)
    # levenshtein_sim = normalized_levenshtein(text1, text2)
    # cosine_sim = cosine_similarity_tfidf(text1, text2)
    fuzz_sim = fuzz_similarity(text1, text2)

    # avg_sim = np.mean([jaccard_sim, levenshtein_sim, cosine_sim, fuzz_sim])

    # avg_sim = round((levenshtein_sim * 100 + fuzz_sim) / 2, 2)

    return fuzz_sim


def get_absolute_similarity_score(text1, text2):
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)
    if text1 == text2:
        return 100
    else:
        return 0


def compare_ob(operation_machine_list, database_records):
    no_of_operations = len(operation_machine_list)
    no_of_operations_ref = len(database_records)

    operation_count = 0

    if no_of_operations <= no_of_operations_ref:
        operation_count = no_of_operations
    else:
        operation_count = no_of_operations_ref

    operation_name_similarity_score = list()
    machine_name_similarity_score = list()

    for i in range(operation_count):
        operation_name = operation_machine_list[i][0]
        machine_name = operation_machine_list[i][1]

        operation_name_ref = database_records[i][0]
        machine_name_ref = database_records[i][1]

        operation_name_score, jaccard_sim, levenshtein_sim, cosine_sim, avg_sim = (
            get_similarity_score(operation_name, operation_name_ref)
        )
        machine_name_score = get_absolute_similarity_score(
            machine_name, machine_name_ref
        )

        # with open("data_analysis.txt", "a") as f:
        #     f.write("====================================================\n")
        #     f.write(
        #         f"Operation Name: \t{operation_name} \nOperation Name Ref: \t{operation_name_ref} \nScore_fuzz: \t{operation_name_score} \nJaccard: \t{jaccard_sim} \nLevenshtein: \t{levenshtein_sim} \nCosine: \t{cosine_sim} \nAvg: \t{avg_sim} \n\n"
        #     )
        #     f.write("====================================================\n")

        operation_name_similarity_score.append(operation_name_score)
        machine_name_similarity_score.append(machine_name_score)

    avg_operation_name_similarity_score = np.mean(operation_name_similarity_score)
    avg_machine_name_similarity_score = np.mean(machine_name_similarity_score)

    avg_total_similarity_score = (
        avg_operation_name_similarity_score + avg_machine_name_similarity_score
    ) / 2

    return {
        "operation_similarity_score": avg_operation_name_similarity_score,
        "machine_similarity_score": avg_machine_name_similarity_score,
        "total_similarity_score": avg_total_similarity_score,
    }


def compare_ob_v2(operation_machine_list, database_records):
    operation_name_similarity_score = list()
    machine_name_similarity_score = list()

    for operation_data in operation_machine_list:
        operation_name = operation_data[0]
        machine_name = operation_data[1]

        operation_name_scores = list()
        machine_name_scores = list()

        for record in database_records:
            operation_name_ref = record[0]
            machine_name_ref = record[1]

            operation_name_score = get_similarity_score(
                operation_name, operation_name_ref
            )
            machine_name_score = get_absolute_similarity_score(
                machine_name, machine_name_ref
            )

            operation_name_scores.append(operation_name_score)
            machine_name_scores.append(machine_name_score)

        max_operation_name_score = max(operation_name_scores)
        max_machine_name_score = max(machine_name_scores)

        operation_name_similarity_score.append(max_operation_name_score)
        machine_name_similarity_score.append(max_machine_name_score)

    avg_operation_name_similarity_score = np.mean(operation_name_similarity_score)
    avg_machine_name_similarity_score = np.mean(machine_name_similarity_score)
    avg_total_similarity_score = (
        avg_operation_name_similarity_score + avg_machine_name_similarity_score
    ) / 2

    return {
        "operation_similarity_score": avg_operation_name_similarity_score,
        "machine_similarity_score": avg_machine_name_similarity_score,
        "total_similarity_score": avg_total_similarity_score,
    }


def get_ob_similarity_score(operation_data, database_records):
    # Data transformation
    operation_machine_list = get_operation_machine_list(operation_data)

    result = list()

    for record in database_records:
        database_record_op_data = record["operation_data"]
        database_record_op_machine_list = get_operation_machine_list_db(
            database_record_op_data
        )

        # similarity_scores = compare_ob(
        #     operation_machine_list, database_record_op_machine_list
        # )
        similarity_scores = compare_ob_v2(
            operation_machine_list, database_record_op_machine_list
        )

        result.append(
            {
                "layout_id": record["layout_id"],
                "layout_code": record["layout_code"],
                "operation_similarity_score": similarity_scores[
                    "operation_similarity_score"
                ],
                "machine_similarity_score": similarity_scores[
                    "machine_similarity_score"
                ],
                "total_similarity_score": similarity_scores["total_similarity_score"],
                # "operation_similarity_score_v2": similarity_scores_v2,
            }
        )

        result.sort(key=lambda x: x["total_similarity_score"], reverse=True)

    return result


def process_record(record, operation_machine_list):
    database_record_op_data = record["operation_data"]
    database_record_op_machine_list = get_operation_machine_list_db(
        database_record_op_data
    )

    similarity_scores = compare_ob_v2(
        operation_machine_list, database_record_op_machine_list
    )

    return {
        "layout_id": record["layout_id"],
        "layout_code": record["layout_code"],
        "operation_similarity_score": similarity_scores["operation_similarity_score"],
        "machine_similarity_score": similarity_scores["machine_similarity_score"],
        "total_similarity_score": similarity_scores["total_similarity_score"],
    }


def get_ob_similarity_score_v2(operation_data, database_records):
    # Data transformation
    operation_machine_list = get_operation_machine_list(operation_data)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(process_record, record, operation_machine_list)
            for record in database_records
        ]
        result = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    result.sort(key=lambda x: x["total_similarity_score"], reverse=True)

    return result
