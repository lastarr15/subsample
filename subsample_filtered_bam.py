import os
import shutil
import random
import pysam
import subprocess
import logging
from logging_setup import sethandlers
sethandlers()

def copy_file(src, dest):
    #Copy a file from src to dest
    try:
        print(f"Copying {src} to {dest}")
        shutil.copyfile(src, dest)
        print(f"Copied {src} to {dest}")
    except Exception as e:
        print(f"Error copying file: {e}")
        raise

def subsample(input_bam, output_bam, target_reads):
    # Subsample the bam file to get the target number of paired reads
    while True:
        # Open the input bam file for reading
        bamfile = pysam.AlignmentFile(input_bam, "rb")

        # Count the total number of paired reads
        total_reads = sum(1 for read in bamfile if read.is_read1 and not read.is_unmapped and not read.mate_is_unmapped)
        bamfile.close()
        print(f"Total paired reads in {input_bam}: {total_reads}")

        if total_reads == 0:
            raise Exception(f"No paired reads found in {input_bam}")

        # Randomly select a start point for subsampling
        start_read = random.randint(0, total_reads - target_reads)
        print(f"Randomly selected start read index: {start_read}")

        # Reopen the bam file and prepare to write the subsampled reads to a temporary file
        bamfile = pysam.AlignmentFile(input_bam, "rb")
        temp_bam_path = f"{output_bam}.temp.bam"
        temp_bam = pysam.AlignmentFile(temp_bam_path, "wb", header=bamfile.header)

        # Initialize variables for tracking read pairs
        read_ids = set()
        idx = 0
        read_pairs = {}
        found_reads = 0

        for read in bamfile:
            if not read.is_paired or read.is_unmapped or read.mate_is_unmapped:
                continue
            if idx < start_read:
                if read.is_read1:
                    idx += 1
                continue

            read_id = read.query_name

            if read_id not in read_pairs:
                read_pairs[read_id] = [None, None]

            if read.is_read1:
                read_pairs[read_id][0] = read
            else:
                read_pairs[read_id][1] = read

            if None not in read_pairs[read_id]:
                # Write the read pair to the temporary bam file
                temp_bam.write(read_pairs[read_id][0])
                temp_bam.write(read_pairs[read_id][1])
                read_ids.add(read_id)
                found_reads += 1

                if found_reads >= target_reads:
                    break

        bamfile.close()
        temp_bam.close()

        if found_reads >= target_reads:
            print(f"Found {found_reads} pairs, subsampling successful.")
            break
        else:
            print(f"Only found {found_reads} pairs, fewer than the target {target_reads}. Retrying...")

    # Write the selected reads to the output BAM file
    bamfile = pysam.AlignmentFile(temp_bam_path, "rb")
    out_bam = pysam.AlignmentFile(output_bam, "wb", header=bamfile.header)

    for read in bamfile:
        if read.query_name in read_ids:
            out_bam.write(read)

    bamfile.close()
    out_bam.close()
    os.remove(temp_bam_path)

    # Validate the output BAM file with samtools flagstat
    validate_bam(output_bam)

def validate_bam(bam_path):
    # Validate the BAM file using samtools flagstat 
    try:
        print(f"Validating {bam_path} with samtools flagstat")
        flagstat_output = subprocess.check_output(['samtools', 'flagstat', bam_path]).decode('utf-8')
        print(flagstat_output)

        # Check that the counts of read1 and read2 are equal
        read1_count = int([line for line in flagstat_output.split('\n') if 'read1' in line][0].split()[0])
        read2_count = int([line for line in flagstat_output.split('\n') if 'read2' in line][0].split()[0])
        if read1_count == read2_count:
            print(f"Validation successful: read1 ({read1_count}) and read2 ({read2_count}) counts are equal.")
        else:
            print(f"Validation failed: read1 ({read1_count}) and read2 ({read2_count}) counts are not equal.")
    except Exception as e:
        print(f"Validation error: {e}")

def subsample_bam(storage_dir, local_dir, bam_file, subsample_sizes):
    # Subsample bam files and move the subsampled files back to the storage directory.
    try:
        bam_path = os.path.join(storage_dir, bam_file)
        local_bam_path = os.path.join(local_dir, bam_file)

        # Copy bam file to local directory for subsampling
        copy_file(bam_path, local_bam_path)

        for size in subsample_sizes:
            subsampled_bam_path = os.path.join(local_dir, f"{bam_file.replace('.bam', '')}_subsampled_{size}.bam")

            # Subsample the bam file keeping paired reads together
            print(f"Subsampling {local_bam_path} to {subsampled_bam_path} with size {size}")
            subsample(local_bam_path, subsampled_bam_path, size)

            # Move the subsampled bam file back to storage directory
            destination_path = os.path.join(storage_dir, os.path.basename(subsampled_bam_path))
            print(f"Moving subsampled BAM {subsampled_bam_path} to {destination_path}")
            shutil.move(subsampled_bam_path, destination_path)
            print(f"Copied subsampled BAM file {destination_path} back to {storage_dir}")

    except Exception as e:
        print(f"An error occurred during subsampling: {e}")

def main():
    # Define directories and subsample sizes
    storage_dir = "/path/to/storage_dir"
    local_dir = "/path/to/local_dir"
    subsample_sizes = [50000, 100000]

    # List all BAM files in the storage directory
    bam_files = [f for f in os.listdir(storage_dir) if f.endswith(".bam")]

    # Process each BAM file
    for bam_file in bam_files:
        subsample_bam(storage_dir, local_dir, bam_file, subsample_sizes)

if __name__ == "__main__":
    main()
