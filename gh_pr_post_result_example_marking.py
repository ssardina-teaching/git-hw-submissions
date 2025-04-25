import logging

# GH emoticons: https://gist.github.com/rxaviers/7360908

# feedback message just after automarker report
FEEDBACK_MESSAGE = r"""

-------------------------
Your code has been automarked for technical correctness and the feedback report is shown above! ☝️ 

As you can see, we’ve crafted a comprehensive set of unit tests to evaluate your code, each with its own description. 😉

The tests are grouped into separate suites corresponding to each question (e.g., db_link, route_ground, etc.). Each suite contains a different number of individual test cases, usually numbered for reference. These tests are designed to assess the correctness of your solution.

Some test cases award points, while others (with scores between -1 and 0) apply a penalty — for example, a score of -0.2 indicates a 20% deduction from the points you’ve earned in that suite.

You will see that some exercises have been splitted into different test suites, for example, the routing predicates have been divided into two suites. Nonetheless, the marks/weights still sum up to original one for the exercise. 👍

The final score (marks) for each suite is based on the total points collected after applying any penalties. The marks are out of 100. A **lot of effort went into designing this system**, and we hope you’ll find it useful as you review your work.

> [!NOTE]
> This is just the automarking part. The final assessment and summary is posted below in a table. 👇
"""

TOTAL_POINTS = 100
FEEDBACK_ENABLED = False
FEEDBACK_ENABLED = True

def report_feedback(marking):
    # if mapping["NOTE-FEEDBACK"]:
    #     mapping["NOTE-FEEDBACK"] = "**" + mapping["NOTE-FEEDBACK"] + "**"

    # no feedback if not enabled
    if not FEEDBACK_ENABLED:
        return None

    # join all the "NOTE-XXXX" fields into a single string
    feedback = ". ".join(
        [marking[x] for x in marking.keys() if "NOTE-" in x and marking[x] != ""]
    )

    # round float values to 2 decimal places
    for k in marking.keys():
        if type(marking[k]) == float:
            marking[k] = round(marking[k], 2)

    return f"""Train Network FEEDBACK & RESULTS 💬
===========

Here is the full summary of your submission, with feedback & marks:

|                                          |                             |
|:-----------------------------------------|----------------------------:|
|**Student number:**                         | {int(marking['STUDENT NO'])} |
|**Student full name:**                      | {marking['Preferred Name']} |
|**Github user:**                            | {marking['GHU']} |
|**Timestamp submission:**                   | {marking['TIMESTAMP']} |
|**Commit marked:**                          | {marking['COMMIT']} |
|**No of commits done:**                     | {marking['SE-COM']} |
|**No of commits expected (low number):**    | {marking['SE-EXCOM']} |
|**Commit ratio (<1 signal problems)**       | {marking['SE-RATIO']} |
|**Days late (if any):**                     | {marking['DYS-LATE']} |
|**Certified?**                              | {marking['CERTIFICATION']} |

**NOTE:** Commit ratio is calculated pro-rata to the points achieved. 
    
## Raw points 🔎
|**Raw points (earned / out of):**      | {marking['TOTAL-PTS']}  | {TOTAL_POINTS} |
|:--------------------------------------|-----------------------|---:|
|**Exercise 1:**                        | {marking['TEX1']}    | 5  |
|**Exercise 2:**                        | {marking['TEX2']}    | 5  |
|**Exercise 3:**                        | {marking['TEX3']}    | 35 |
|**Exercise 4:**                        | {marking['TEX4']}    | 30  |
|**Exercise 5:**                        | {marking['TEX5']}    | 25 |
    
## Development Quality (discount) weights (if any) 🕵🏽‍♂️
|**Level of problem (if any):**             | {marking['SE-STATUS']} |
|:------------------------------------------|---------------------:|
|**Merged feedback PR:**                    | {marking['SE-MERGE']} |
|**Forced push:**                           | {marking['SE-FORCE']} |
|**Commits with invalid username:**         | {marking['SE-GHU']} |
|**Printout side-effects (debug code?):**   | {marking['SE-LARGE']} |
|**Commit number/process:**                 | {marking['SE-LRATIO']} |
|**Other quality issues:**                  | {marking['SE-OTHER']} |
|**Issues with development?:**              | {marking['SE-STATUS']} |
    
## Summary of results 🏁
| -----------------------------------------------------  |                       |
|:------------------------------------------|----------------------:|
|**Raw points (out of {TOTAL_POINTS}):**    | {marking['TOTAL-PTS']}  |
|**Raw marks (out of 100):**                | {marking['MARKS-RAW']} |
|**Marks adjustments (if any):**            | {marking['MARKS-ADJ']} |
|**Late penalty marks (10/day, if any):**   | {marking['MARKS-LATE']} |
|**Development weight adjustment (if any):**| {marking['WEIGHT-SE']} |
|**Other weight adjustments (if any):**     | {marking['WEIGHT-OT']} |
|**Total weight (1, if none):**             | {marking['WEIGHT']} |
|**FINAL MARKS (out of 100):**              | **{marking['MARKS-F']}** |
|**FINAL GRADE**                            | **{marking['GRADE']}** |
|**General feedback:**                      | {marking['FEEDBACK']}|
|**Marking feedback report:**               | See comment before :-)|
|**Additional notes, observations**         | {feedback} |

The final marks (out of 100) is calculated as follows:

* **FINAL MARKS** = (Raw Marks + Marks Adjustments + Late Adjustments) * Total Weight
* Total Weight is between 0 and 1; with 1 if no adjustments.

As we explained in class, each unit test is judged on soundness (-70% if fails soundness), completeness (90%), and non-redundant answers (10%). 

Detailed explanation of the marking and report can be found in [HERE](https://github.com/RMIT-COSC2780-2973-IDM25/IDM25-DOC/blob/main/MARKING-TRAIN.md). Also refer to post [#57](https://edstem.org/au/courses/22051/discussion/2596224) and [#58](https://edstem.org/au/courses/22051/discussion/2596515) for more details on the marking process and overall results.

**Hope the above feedback is clear and detailed.** 🤞

Remember the SE/GIT development aims to have minimal **evidence of the process towards the solution in your development**. The expected commits is a bare minimum that serves as _proxy_ to signal a problem, not an aim in itself (that is why it is so low). As a reference, the average number of commits was around 30, and submissions that achieved high-scores (85+) had 50+ commits. We used a **very low bound of 15 commits** for a _perfect solution_ (pro-rata on points achieved); less than sugests problem with development.  ✔️

This concludes the assessment.

🙏 Thanks for your submission & hope you enjoyed and learnt from this project! 🙏

**Sebastian**

> [!WARNING]
> **Please do not send emails or post about your submission or results on the forum**. Only questions, challenges, or comments posted below in this pull request 👇 will be considered.
> 
> Your message must include clear evidence that you have thoroughly reviewed the report and your solution. Submissions that do not demonstrate thoughtful analysis will be ignored.

Sebastian
"""


# def no_tag_feedback(mapping):
#     return f"""Project 2 FEEDBACK & RESULTS

# https://github.com/RMIT-COSC1127-1125-AI24/AI24-DOC/blob/main/FAQ-PROJECTS.md#i-submitted-wrongly-eg-didnt-tag-correctly-and-is-now-after-the-due-date-can-you-consider-my-submission💬


def check_submission(repo_id: str, marking: dict, logger: logging.Logger):
    """Checks on the submission for the repo_id and returns a message and a skip flag, if applicable.

    The markign_repo is the row in the marking spreadsheet and may contain columns that signal problems with the submission.
    (e.g., no certification, no tag, etc.)
    """
    message = None
    skip = False
    if not marking["COMMIT"]:
        logger.warning(f"\t Repo {repo_id} has no tag submission.")
        message = (
            f"Dear @{repo_id}: no submission tag found; no marking as per spec. :cry:"
        )
        message = f"Dear @{repo_id}: no submission tag found, so nothing to mark. :cry: If you still want to submit (albeit with a discount), [check this](https://tinyurl.com/22r4j6t8)."
        skip = True
    elif marking["CERTIFICATION"].upper() != "YES":
        logger.warning(f"\t Repo {repo_id} has no certification.")
        message = f"Dear @{repo_id}: no certification found; no marking as per spec. :cry: If you still want to submit with an existing commit, please fill certification and let us know in this PR; we will remark it, albeit with a discount late penalty (certification is in the submission instructions and has been discussed a lot)."
        skip = True
    elif "SKIP" in marking and marking["SKIP"]:
        logger.warning(
            f"\t Repo {repo_id} is flagged to be SKIPPED...: {marking['SKIP']}"
        )
        skip = True
    return message, skip
