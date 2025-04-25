import logging
# GH emoticons: https://gist.github.com/rxaviers/7360908

# no report - no feedback
FEEDBACK_MESSAGE = None

REPOS = [
"anurag060197",
"aswin01399",
"baoly19",
"devikaps",
"gamemumu",
"jerrytheo28",
"krisanahari",
"liuwei03200",
"marmaladian",
"meenusingh123",
"moncy - code",
"orhaus",
"param - kasana",
"rafaelperez375",
"rankun203",
"rhutwi",
"sakshamjain2552",
"shan250700",
"sheikhmunim",
"spoo24",
"sreerajhere",
"tanishachaudhary23",
"venthryn",
"xalien123",
"ninjakid07",
"omkadam7",
"pranjolm",
"sahil22student13",
"shrestharushika",
"stormragekk",
"juliannethomas",
"thearft"]

def get_repos():
    return REPOS


def report_feedback(marking: dict):

    return f"""
Hi @{marking['GHU']}, 

Just a note that the commit sha marked last was {marking['COMMIT']} with tag `resubmission`. 👍 
(The one in the summary table above may be wrong and refers to the original submission!)  
"""


def check_submission(repo_id: str, marking: dict, logger: logging.Logger):
    """Checks on the submission for the repo_id and returns a message and a skip flag, if applicable.

    The marking_repo is the row in the marking spreadsheet and may contain columns that signal problems with the submission.
    (e.g., no certification, no tag, etc.)
    """
    message = None
    skip = False
    if "SKIP" in marking and marking["SKIP"]:
        logger.warning(
            f"\t Repo {repo_id} is flagged to be SKIPPED...: {marking['SKIP']}"
        )
        skip = True
    return message, skip
