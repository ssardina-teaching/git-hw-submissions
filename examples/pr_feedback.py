import logging


FEEDBACK_MESSAGE = """

-------------------------
Your code has been automarked for technical correctness and your grades are now preliminary registered!

Please note the following:

- We will be running code similarity checks, as well as inspecting reports and code manually, in an ongoing basis for all the projects. We reserve the right to adjust the marks or to have a demo meeting with you, if necessary.
- The total points above is raw and does not reflect the weighting of each question (as per spec.).

Thanks for your submission & hope you enjoyed and learnt from this Pacman Search project!

Sebastian & Andrew
"""

TOTAL_POINTS = 25


def report_feedback(row):
    if row["NOTE-FEEDBACK"]:
        row["NOTE-FEEDBACK"] = "**" + row["NOTE-FEEDBACK"] + "**"

    # join all the "NOTE-XXXX" fields into a single string
    feedback = " ".join([row[x] for x in row.keys() if "NOTE-" in x])

    for k in row.keys():
        if type(row[k]) == float:
            row[k] = round(row[k], 2)

    return f"""Project 2 FEEDBACK & RESULTS 💬
===========

|                                          |                             |
|:-----------------------------------------|----------------------------:|
|**Student number:**                         | {row['STUDENT NO']} |
|**Student full name:**                      | {row['Preferred Name']} |
|**Github user:**                            | {row['GHU']} |
|**Git repo:**                               | {row['URL-REPO']} |
|**Timestamp submission:**                   | {row['TIMESTAMP']} |
|**Commit marked:**                          | {row['COMMIT']} |
|**No of commits:**                          | {row['SE-NOCOM']} |
|**Commit ratio (<1 signal problems)**       | {row['SE-RATIO']} |
|**Days late (if any):**                     | {row['DYS LATE']} |
|**Certified?**                              | {row['CERTIFICATION']} |

**NOTE:** Commit ratio is calculated pro-rata to the points achieved.

## Raw points 🔎
|**Raw points (earned / out of):**      | {row['RPOINTS']}  | {TOTAL_POINTS} |
|:--------------------------------------|-----------------------|---:|
|**Q1:**                                | {row['Q1T']}      | 4  |
|**Q2:**                                | {row['Q2T']}      | 5  |
|**Q3:**                                | {row['Q3T']}      | 5  |
|**Q4:**                                | {row['Q4T']}      | 5  |
|**Q5:**                                | {row['Q5T']}      | 6  |


## Software Engineering (SE) (discount) weights (if any) 🕵🏽‍♂️
|**Level of problem (if any):**             | {row['SE-STATUS']} |
|:------------------------------------------|---------------------:|
|**Merged feedback PR:**                    | {row['SE-PRMER']} |
|**Forced push:**                           | {row['SE-FORCED']} |
|**Commits with invalid username:**         | {row['SE-GHUSR']} |
|**Printout side-effects (debug code?):**   | {row['SE-LARGE']} |
|**Commit number/process:**                 | {row['SE-LOWRAT']} |
|**Other quality issues:**                  | {row['SE-OTHR']} |

## Summary of results 🏁
|                                           |                       |
|:------------------------------------------|----------------------:|
|**Raw points collected (out of {TOTAL_POINTS}):**      | {row['RPOINTS']}  |
|**Other discount weight (if any):**        | {row['WEIGHT-M']}   |
|**Total weight adjustment (1 if none):**   | {row['WEIGHT']}   |
|**Raw marks (out of 100):**                | {row['RAW-MARKS']}    |
|**Late penalty (10/day, if any):**         | {row['LATE-PEN']} |
|**Final marks (out of 100):**              | **{row['MARKS']}**    |
|**Grade:**                                 | **{row['GRADE']}**    |
|**Marking report:**                        | See comment before :-)|
|**Notes (if any)**                         | {feedback}      |

The final marks (out of 100) is calculated as follows: 📱

* **RAW MARKS** = ((RAW_POINTS / TOTAL_POINTS)*TOTAL_WEIGHT_ADJUSTMENT)*100
* **FINAL MARKS** = RAW MARKS - LATE PENALTY

For more information on marking scheme, refer to post [#252](https://edstem.org/au/courses/15662/discussion/2190239).

Hope the above feedback is clear and detailed🤞, but if you spot any factual error in the marking or you really need clarification (after carefully analysing the feedback), please **post HERE in this PR** 👇🏾: _do not send email or make posts in the forum_.

Sebastian
"""


def check_submission(repo_id: str, row: dict, logger: logging.Logger):
    """Checks on the submission for the repo_id and returns a message and a skip flag, if applicable.

    The row is the row in the marking spreadsheet and may contain columns that signal problems with the submission (e.g., no certification, no tag, etc.).
    """
    message = None
    skip = False
    if not row["COMMIT"]:
        logger.warning(f"\t Repo {repo_id} has no tag submission.")
        message = (
            f"Dear @{repo_id}: no submission tag found; no marking as per spec. :cry:"
        )
        message = f"Dear @{repo_id}: no submission tag found, so nothing to mark. :cry: If you still want to submit (albeit with a discount), [check this](https://bit.ly/3XoMSsf). Note this was discussed a lot, including at lectorial; see [slide](https://bit.ly/4e7a2sB))."

        skip = True
    elif row["CERTIFICATION"].upper() != "YES":
        logger.warning(f"\t Repo {repo_id} has no certification.")
        message = f"Dear @{repo_id}: no certification found; no marking as per spec. :cry: If you still want to submit, please fill certification and let us know in this PR; we will remark it, albeit with a discount late penalty (certification is in the submission instructions and has been discussed a lot, including at lectorial; see [slide](https://bit.ly/4e7a2sB))."
        skip = True
    elif row["SKIP"]:
        logger.warning(f"\t Repo {repo_id} is flagged to be SKIPPED...: {row['SKIP']}")
        skip = True
    return message, skip
