import os
import shutil
import subprocess
import logging
from logging_setup import sethandlers
sethandlers()

def copy_filter_copy(storage_dir, local_dir, bam_file, quality_threshold):
    try:
        # Construct full paths for source and destination BAM files
        bam_gz_path = os.path.join(storage_dir, bam_file)
        local_bam_gz_path = os.path.join(local_dir, bam_file)

        # Copy the .bam.gz file from the storage directory to the local directory
        logging.info(f"Copying {bam_file} from {bam_gz_path} to {local_bam_gz_path}")
        shutil.copyfile(bam_gz_path, local_bam_gz_path)
        logging.info(f"Copied {bam_file} to {local_dir}")

        # Unzip the copied .bam.gz file
        logging.info(f"Unzipping {local_bam_gz_path}")
        subprocess.run(['gzip', '-d', local_bam_gz_path], check=True)
        logging.info(f"Unzipped {local_bam_gz_path}")

        # Prepare the path for the unzipped BAM file
        local_bam_path = os.path.splitext(local_bam_gz_path)[0]  # Remove the .gz extension
        bam_file_name = os.path.basename(local_bam_path).replace(".bam", "")  # Remove .bam extension

        # Construct the path for the filtered BAM file
        filtered_bam_path = os.path.join(local_dir, f"{bam_file_name}_filtered.bam")

        # Filter the BAM file using samtools to include only paired reads with the desired quality
        logging.info(f"Filtering {local_bam_path} to {filtered_bam_path}")
        subprocess.run(['samtools', 'view', '-h', '-f', '1', '-q', str(quality_threshold), '-b', '-o', filtered_bam_path, local_bam_path], check=True)
        logging.info(f"Filtered paired reads and applied quality filter, saved to {filtered_bam_path}")

        # Move the filtered BAM file back to the storage directory
        destination_path = os.path.join(storage_dir, os.path.basename(filtered_bam_path))
        logging.info(f"Moving {filtered_bam_path} to {destination_path}")
        shutil.move(filtered_bam_path, destination_path)
        logging.info(f"Copied quality-filtered BAM file {destination_path} back to {storage_dir}")
    
    except subprocess.CalledProcessError as e:
        # Log errors related to subprocess calls
        logging.error(f"Error running subprocess: {e}")
    except Exception as e:
        # Log any other errors
        logging.error(f"An error occurred: {e}")

def main(storage_dir, local_dir, quality_threshold):
    # List all .bam.gz files in the storage directory
    bam_files = [f for f in os.listdir(storage_dir) if f.endswith(".bam.gz")]

    # Process each BAM file
    for bam_file in bam_files:
        copy_filter_copy(storage_dir, local_dir, bam_file, quality_threshold)

if __name__ == "__main__":
    
