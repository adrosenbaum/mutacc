import subprocess
import logging
from pathlib import Path

LOG = logging.getLogger(__name__)

def bam_to_fastq(bam, fastq1, fastq2, picard_exe=None):
    """
        Converts bam file two paired end fastqs, using picard's SamToFastq

        Args:
            bam (path): name of bam file
            fastq1 (path): name of output fastq file for first end
            fastq2 (path): name of output fastq file for second end
            picard_exe (path): path to picard executable
    """

    if picard_exe:
        picard_base = ['java', '-jar', str(picard_exe)]
    else:
        picard_base = ['picard']

    picard_cmd = picard_base + [
        'SamToFastq',
        'VALIDATION_STRINGENCY=LENIENT',
        'I=' + bam,
        'F=' + fastq1,
        'F2=' + fastq2
    ]

    exit_status = subprocess.call(picard_cmd)

    if exit_status != 0:

        LOG.critical("{} failed to run".format(
                " ".join(picard_cmd)
            )
        )

        raise subprocess.CalledProcessError(
            returncode=exit_status,
            cmd = " ".join(picard_cmd)
            )


    #Make sure fastq files have been created
    exists_1 = Path(fastq1).exists()
    exists_2 = Path(fastq2).exists()

    if not (exists_1 and exists_2):

        LOG.critical("{} failed to run".format(
                " ".join(picard_cmd)
            )
        )

        raise Exception
