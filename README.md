This can be used to down sample bam files to a desired number of reads. This pipeline was designed to keep paired-end reads together and subsample the bam files from a randomly selected start site. 
The bam files must first be filtered for paired reads using samtools, and then can be subsampled accordingly using pysam. 
