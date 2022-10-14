# From DICOM to Nifti:
## Pipeline for converting Raystation dicom exports into anonymized niftis for use in ITK-SNAP and bespoke MATLAB app

### System Requirements:

### Destination File Structure:
All of the niftis generated through useage of this code are automatically saved into a user-specified directory (e.g. /Users/sblackledge/Documents/nifti_dump). The code will automatically create 'images' and 'masks' sub-directories. Each of these sub-directories will contain additional sub-directories corresponding to the user-specified patient name (e.g. 'g01', 'g02, etc.). The figure below demonstrates the final hierarchy:

![This is an image](https://github.com/sarahannblackledge/GENIUSII/blob/master/directory_hierarchy.png)

### Step 1: Export clinical dicoms from RayStation to local machine
By 'clinical 'dicoms', I am referring to the following:
  1. The full-bladder planning CT and corresponding RTSTRUCT (containing target, OARs, and PTVs)
  2. All desired CBCTs and corresponding registrations (denoted as 'REG' on the Raystation export window). Note: the registrations are obtained by  importing the CBCTS from Mosaiq using the 'import XVI' script in Clinical Raystation. These registrations are critical because they represent the CBCT-to-CT registrations performed clinically.

The export pipeline should be as follows:
Mosaiq ==> Clinical Raystation (not anonymized) ==> Research Raystation (not anonymized) ==> rtp-bridge (anonymized*) ==> Local machine

*Be sure to tick the 'Anonymization' export box when exporting from Research Raystation, but set the following:
  1. Patient Name: gXX (i.e. g02)
  2. Patient ID: GENIUSII
  3. **Tick 'Retain dates' and 'Retain UIDs'**

Note: On the bridge/local machine, each patient's clinical dicoms need to be saved in a unique folder. Don't lump all of the patients together into one huge dicom dump.

### Step 2: Convert clinical dicom data dumped within specified patient directory (Local machine) into niftis organized by patient name and date
Upon successul export of the clinical dicom data, your patient folder should contain a massive set of dicom files (CT1.X.XX.XXXX, REG1.X.XX, RS1.X.XX...). Run the following code to read in these files and save as organized niftis:

1. raystation_dcmDump_to_nifi.py





