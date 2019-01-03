# mutacc
[![Build Status](https://travis-ci.org/Clinical-Genomics/mutacc.png)](https://travis-ci.org/Clinical-Genomics/mutacc)
[![Coverage Status](https://coveralls.io/repos/github/Clinical-Genomics/mutacc/badge.svg?branch=master)](https://coveralls.io/github/Clinical-Genomics/mutacc?branch=master)

## The mutation accumulation database

mutacc is a tool that makes it possible to create synthetic datasets to be used
for quality control or benchmarking of bioinformatic tools and pipelines intended
for variant calling. Using raw reads that supports a known variant from a real
NGS data, mutacc creates validation sets with true positives with the same
properties as a real NGS data.

## Installation
### Conda
For installation of mutacc and the external prerequisites, this is made easy by creating 
conda environment

```consol
conda create -n <env_name> python=3.6 pip numpy cython
```

activate environment

```consol
source activate <env_name>
```
### External Prerequisites
mutacc takes use of two external packages, seqkit, and picard. These can be installed 
within a conda environment by

```bash
conda install -c bioconda picard
conda install -c bioconda seqkit
```

### Install mutacc
Within the conda environment, do
```bash
git clone https://github.com/adrosenbaum/mutacc
pip install -e mutacc
```
## Usage

### Populate the mutacc database

To export data sets from the mutacc DB, the database must first be populated. To
extract the raw reads supporting a known variant, mutacc takes use of all
relevant files generated from a NGS experiment up to the variant calling itself.
That is the bam file, and vcf file containing only the variants of interest.

This information is specified as a 'case', represented in yaml format

```yaml
#EXAMPLE OF A CASE

#THE CASE FIELD CONTAINS METADATA OF THE CASE ITSELF
case:
    case_id: 'case123' #REQUIRED CASE_ID

#LIST OF THE SAMPLES INVOLVED IN THE EXPERIMENT (MAY BE ONE, OR SEVERAL, E.G.
#A TRIO)
samples:
  - sample_id: 'sample1' #REQUIRED
    analysis_type: 'wgs' #REQUIRED
    sex: 'male'          #REQUIRED
    mother: 'sample2'    #REQUIRED (CAN BE 0 if no mother)
    father: 'sample3'    #REQUIRED (CAN BE 0 if no father)
    bam_file: /path/to/sorted_bam #REQUIRED
    phenotype: 'affected'

  - sample_id: 'sample2'
    analysis_type: 'wgs'
    sex: 'female'        
    mother: '0' #0 if no parent            
    father: '0'         
    bam_file: /path/to/sorted_bam
    phenotype: 'unaffected'

  - sample_id: 'sample2'
    analysis_type: 'wgs'
    sex: 'male'         
    mother: '0'             
    father: '0'            
    bam_file: /path/to/sorted_bam
    phenotype: 'affected'

#PATH TO VCF FILE CONTAINING VARIANTS OF INTEREST FROM CASE
variants: /path/to/vcf
```

This will find the reads from the bam files specified for each sample. If it
is desired that the reads are found from the fastq files instead, this can be
done by specifying the fastq files as such

```yaml
  - sample_id: 'sample1'
    analysis_type: 'wgs'
    sex: 'male'          
    mother: 'sample2'    
    father: 'sample3'    
    bam_file: /path/to/sorted_bam
    fastq_files:
      - /path/to/fastq1
      - /path/to/fastq2
    phenotype: 'affected'
```
To extract the reads from the case

```console
mutacc extract --padding 600 --case <case.yaml> --mutacc-dir <dir> --out-dir <dir>
```
the --padding option takes the number of basepairs that the desired region is
padded with.

The option --mutacc-dir specifies the directory where the extracted reads are stored. The extracted reads are stored in fastq format.

This will create a file 'case_id'.mutacc stored in the directory specified with the --out-dir option.

To import the case into the database

```console
mutacc db import case_id.mutacc
```

The db command is called each time mutacc needs to do any operation against the database.

This will try to establish a connection to an instance of mongodb, by default
running on 'localhost' on port 27017. If this is not wanted, it can be specified
with the --host and --port options.



```console
mutacc db -h <host> -p <port> import case_id.mutacc
```

If authentication is required, this can be specified with the --username and
--password options.

or in a configuration file e.g.
```yaml
#EXAMPLE OF A CONFIGURATION FILE
host: <host>
port: <port>
username: <username>
password: <password>
```

```console
mutacc --config-file <config.yaml> db import case_id.mutacc
```


### Export datasets from the database
The datasets are exported one sample at the time. At the moment, mutacc only
supports father/mother/child-trios and single samples. To export a synthetic
dataset, the export command is used together with options.

export:

  -m/--member [child|father|mother|affected]
    specifies what family member to create a dataset for. Finds the correct
    member in each case (if trio) in the database, and uses the reads from this
    sample only to enrich the background samples. If a single sample dataset is
    required, the option can be passed with the 'affected' argument, use the
    reads from only one of the affected samples from each case.

  -c/--case-query \
    Query to search among the case collection in the mongodb. A json string,
    with valid mongodb query language.

  -v/--variant-query \
    Query to search among the variants collection.

  
  
  -s/--sex [male|female] \
    Specify the sex of the sample
    
  -n/--sample-name \
    name of the sample
    
  -p/--proband \
    This flag will make the sample 'proband', this will force all variants from 
    single cases to be included into this sample
    
  --vcf-dir \
    Specify the directory where the vcf file is stored. (can be specified in config file as 'vcf_dir')
    
  --merge-vcf \
    If the generated vcf needs to be merged with another vcf
    
  --out-dir \
    Specify the directory where the export object file is stored (can be specified in config file as 'query_dir')
    

example:

```console
mutacc --config-file <config.yaml> db export -m affected -c '{}' 
```
will find all the cases from the mutacc DB, and store this 
information in a file <out_dir>/sample_name_query.mutacc.

to export a entire trio, this can be done by

```console
mutacc --config-file <config.yaml> db export -m child -c '{}' -p -n child
mutacc --config-file <config.yaml> db export -m father -c '{}' -n father
mutacc --config-file <config.yaml> db export -m mother -c '{}' -n mother
```
This will create three files in the directory specified with the --out-dir option 
(or in the config file); child_query.mutacc, father_query.mutacc, and mother_query.mutacc. 

To make a dataset (fastq-files) from a query object the synthesize command is used 
with the following options

   -b/--background-bam \
    Path to the bam file for sample to be used as background

  -f/--background-fastq \
    Path to fastq file for sample to be used as background

  -f2/--background-fastq2 \
    Path to second fastq file (if paired end experiment)
    
  -q/--query \
    Path to the query files created with the export command
    
  --out-dir \
    Directory where fastq files will be stored (Can be in config file as 'dataset_dir')
    
  --tmp_dir \
    Directory where temporary files will be stored. i.e. the background 
    files with the excluded reads (Can be in config file as 'tmp_dir')

example, using the query files created above

```console
mutacc --config-file <config.yaml> synthesize -b <bam> -f <fastq1_child> -f2 <fastq2_child> -q child_query.mutacc
mutacc --config-file <config.yaml> synthesize -b <bam> -f <fastq1_father> -f2 <fastq2_father> -q father_query.mutacc
mutacc --config-file <config.yaml> synthesize -b <bam> -f <fastq1_mother> -f2 <fastq2_mother> -q mother_query.mutacc
```

The created fastq-files will be stored in the directory specified by the --out-dir option.

### Remove case from database

To remove a case from the mutacc DB, and all the generated bam, and fastq files
generated from that case from disk, the remove command is used

```console
mutacc --config-file <config.yaml> db remove <case_id>
```

## Limitations

mutacc is currently under development and only supports either single cases
(cases with one sample) or mother/father/child trios. Furthermore, all cases
uploaded, and exported from the mutacc DB are assumed to be paired-end reads
experiments. 
