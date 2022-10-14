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

  Inputs:
  
    1. ct_directory: str - full filepath where data exported from RayStation are stored. This contains a dump of 
    all CBCT, CT, RTSTRUCT, and REG dicoms, and is not organized in an intuitive way.
    Example: ct_directory =  '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g02/Raystation_CTdump'
    
    2. save_dir: str - full filepath where nifti files should be saved. 
    Example: save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump'
    
    3. patient_name: str - string indicating name of patient. Example: 'g02'

Output:
    Nifti file for every (1) dcm image dataset and (2) relevant structure from the RTSTRUCT.dcm file exported from RayStation
    Note: no date or name information is stored in the metadata of these nifti files, so they are considered fully anonymized.
    HOWEVER, the nifti filename contains the study date by default. I recommend changing this manually retrospectively once
    all desired data has been converted to nifti format (e.g. Fraction1.nii.gz).

### Step 3: Format ultrasound data for export to RayStation
On the Clarity workstation, you need to apply the couch shifts to the corresponding US image so that the ultrasounds are in the same frame of reference as the corresponding CBCT and CT SIM. Instructions for this are on the workstation Desktop. Once these shifts have been applied and the resulting images saved as 'contouring workspaces', these can be exported to Research Raystation. They are not anonymized, so can be linked up with the CT/CBCT data previously imported. Note: the only reason that we need to export to Raystation is so that Clarity will automatically convert the images into the dicom file format with the desired registrations applied. Direct export from Clarity will result ultrasounds saved in the so-called 'usf' file format in which US images are still in polar coordinates in the native frame of reference. Also note: the ultrasounds show up in the RayStation 'data management' tab in the order in which they were exported -- NOT the order in which they were acquired. 

### Step 4: Export US data from Raystation to your local machine

The export pipeline should be as follows:
Research Raystation (not anonymized) ==> rtp-bridge (anonymized*) ==> Local machine

*Be sure to tick the 'Anonymization' export box when exporting from Research Raystation, but set the following:
  1. Patient Name: gXX (i.e. g02)
  2. Patient ID: GENIUSII
  3. **Tick 'Retain UIDs'**

Note: there is no date information in the US dicom metadata when exported from Clarity to RayStation. Although it is theoretically possible to sort through a huge dump of US dicom data and determine which individual files correspond to a single 3D image, it is *impossible* to trace back which date/fraction these images came from. Therefore, the export process in this step is quite tedious, as each US 

