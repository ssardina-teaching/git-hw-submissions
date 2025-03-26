import argparse
import os
import shutil
import sys
import zipfile
import re
import logging


# logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.DEBUG, datefmt='%a, %d %b %Y %H:%M:%S')


"""
This script takes a list of zip files submitted (sXXXXXX_2017-03-25T10:35:06.132000+11:00) and unzips its content into XXXXXX
"""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='This script takes submitted files with .zip extensions and produces directories for each student number\n',
        # formatter_class = argparse.RawTextHelpFormatter
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'SUBDIR',
        type=str,
        default='./',
        help='Directory where zip files are located.'
    )
    parser.add_argument(
        'OUTPUTDIR',
        type=str,
        default='./',
        help='Directory where student directories will be placed.'
    )
    parser.add_argument(
        '--ext',
        type=str,
        required=False,
        default='zip',
        help='Extension of submission files to gather.'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        default=False,
        help='Overwrite destination if exists.'
    )
    args = parser.parse_args()
    print(args)

    if not os.path.exists(args.SUBDIR) or not os.path.isdir(args.SUBDIR):
        logging.error(
            f'Submissions directory not found or correct: {args.SUBDIR}')
        sys.exit(1)

    if not os.path.exists(args.OUTPUTDIR) or not os.path.isdir(args.OUTPUTDIR):
        logging.error(
            f'Submission output directory not found or correct: {args.OUTPUTDIR}.')
        sys.exit(1)

    # e.g., s3900792_2021-06-16T20:39:25.689000+10:00.zip
    # we will keep whatever is before the first _, that is s3900792
    sub_filename_pattern = re.compile(rf'(.+)_(.+).{args.ext}')

    # get all file names in submission folder
    file_names = next(os.walk(args.SUBDIR))[2]
    for file_name in file_names:
        try:
            match = re.match(sub_filename_pattern, file_name)
            # keep the prefix "s3900792" from filename
            student_dir = match.group(1)
            path_file = os.path.join(args.SUBDIR, file_name)
            path_dest_student_dir = os.path.join(args.OUTPUTDIR, student_dir)
            if not os.path.exists(path_dest_student_dir) or args.overwrite:
                if not os.path.exists(path_dest_student_dir):
                    os.mkdir(path_dest_student_dir)
                try:
                    student_zip_file = zipfile.ZipFile(path_file)
                    student_zip_file.extractall(path_dest_student_dir)
                    logging.info(
                        f'Submission zip {file_name} EXPANDED into {path_dest_student_dir}')
                except zipfile.BadZipFile:
                    logging.info(
                        f'Submission {file_name} COPIED into {path_dest_student_dir}')
                    shutil.copy(path_file, path_dest_student_dir)
                except Exception as e:
                    logging.error(
                        f'Unable to process file {file_name}: {type(e)} ({e})')
                    os.rmdir(path_dest_student_dir)
        except Exception as e:
            print(type(e))
            logging.warning(
                f"File {file_name} cannot be processed at all (not maching pattern?): {e}")
