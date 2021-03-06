# MutAcc Demo

To get an intuition over how MutAcc works, this demo provides a fast go through of the main features.

Files that can be used in this demo are found in the ```mutacc/resources/``` folder in the root of this repository. These files are simulated fastq, and bam-files that represents a father/mother/child trio. The files cover a 2000 bp region of the CFTR gene, with 200 paired reads for each file 2*151bp. The fastq files were generated using [wgsim](https://github.com/lh3/wgsim), and the bam files were generated aligning these fastq-files with [bwa](https://github.com/lh3/bwa) against the [GRCh37](https://www.ensembl.org/info/website/tutorials/grch37.html) reference. The child has a simulated de-novo heterozygous SNV 7:117235031 G->A. This demo shows how this family, along with the causative clinical variant can be uploaded into the mutacc database, and later exported to create a new synthethic sample.

in this demo, the flag ```-d/--demo``` is used after the main command , i.e. ```mutacc --demo [subcommands] [options]```. With this flag, no configuration file will be necessary. This will create the mutacc root directory in the current working directory ```./mutacc_demo_root/``` which can be removed after the demo is completed. For this demo to work, it requires that a mongodb process is running on host 'localhost' and 27017. If mutacc is installed on a conda environment (which is recommended!) source the environment before starting this demo. Don't forget to ```cd``` into a directory where the root ```mutacc_demo_root``` is to be made.

## Extract reads from case

Before this family can be uploaded into the database, the reads from overlapping the given causative variant (specified in ```mutacc/resources/variant1.vcf.gz```) must be extracted. This is done with the following command

 ```terminal
 mutacc --demo extract --padding 100
 ```

have a look at the ```mutacc/resources/case.yaml``` file. Here all paths to bam-files and the vcf containing
the causative variant are given, along with other meta-data.

This will extract all reads spanning the variant position with an additional padding
of 100 bp on both sides. The variant reads will be placed in ```./mutacc_demo_root/reads/demo_trio/<sample>/<date>/``` as fastq.gz files. There will also be a new json formatted file in ```./mutacc_demo_root/imports/demo_trio_import_mutacc.json``` that can now be uploaded into the database.

## Upload case to the database

The upload is done with one simple command

```terminal
mutacc --demo db import ./mutacc_demo_root/imports/demo_trio_import_mutacc.json
```

The information in the .json file will now get imported into the database

## Query the database

Congrats! there is now one case and one variant in the database. These can now be queried for
with the command

```terminal
mutacc --demo db export --case-query '{}' --member child --proband --sample-name child
```

Let's go through the options given in this example.

--case-query '{}': This option will take a json-formated string. When making queries
mutacc uses the [mongodb](https://docs.mongodb.com/manual/) query language, where all
queries are specified as json objects. giving the string '{}' which is an empty json object
will return all cases in the database. the user can also choose to query on variants with
the --variant-query option.

--member child: This specifies that we are interested in child samples. Other valid values
for this option are 'father', 'mother', and 'affected'

--proband: This flag specifies that the exported sample will be proband. This will come in handy when there are several cases in the database, where some are not father/mother/child-trios. With this flag activated, the samples will be queried even if it is not of type 'child' (Single sample cases do not have any sample marked as child).

--sample-name child: This allows the User to specify a name for the exported sample. In this case 'child'

First look in ```./mutacc_demo_root/variants/child_variants.vcf```. Here a vcf has been created with all variants through the query.

Another file ```./mutacc_demo_root/queries/child_query_mutacc.json``` has also been created.
This file will be used to create our synthetic samples in the next section.

## Create datasets

To create a synthetic dataset, the user must chose a background that will be enriched
with the reads from our query. Let's try to enrich the fastq-files of the father with the reads of his child.

```terminal
mutacc --demo synthesize --query ./mutacc_demo_root/queries/child_query_mutacc.json
```

This will create two fastq files in ```./mutacc_demo_root/datasets/```. These files now have the reads from the child spanning the variant region, flanked by the reads from the originial ```mutacc/resources/father.fastq.gz``` file.

To visualize this, one can align the generated dataset against a reference and show the generated bam file in [igv](https://igv.org). Below is an example of our synthetic dataset, along with the original datasets for the father and the child.

![alt text](igv_snapshot.png)

Why is this useful? Imagine that the database contain a large number of clinical cases with known clinical variants. MutAcc can, by following the same workflow as above, create synthetic datasets by enriching well known genomic data with real clinical variants. These synthetic datasets can be used in validation of bionformatics pipelines that are used for clinical purposes.
