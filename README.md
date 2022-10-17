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
Upon successul export of the clinical dicom data, your patient folder should contain a massive set of dicom files (CT1.X.XX.XXXX, REG1.X.XX, RS1.X.XX...). Run the following code to convert the dicoms into nifti files and automatically save them in the 'images' and 'masks' sub-directories corresponding to your patient name (see Destination File Structure). 

**Modify sys.path.append line?**

1. raystation_dcmDump_to_nifi.py

  Inputs:
  
    1. ct_directory: str - full filepath where data exported from RayStation are stored. This contains a dump of 
    all CBCT, CT, RTSTRUCT, and REG dicoms, and is not organized in an intuitive way.
    Example: ct_directory =  '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g02/Raystation_CTdump'
    
    2. save_dir: str - full filepath where nifti files should be saved. 
    Example: save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump'
    
    3. patient_name: str - string indicating name of patient. Example: 'g02'
    
    4. masks_of_interest: list of strings: exact names of masks that should be exported and saved as niftis.
    Example: masks_of_interest = ['Bladder', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum', 'CTV-E', 'CTV-T HRinit', 'CTV-T LRinit_1_Full']

Output:

    .nii.gz file for every (1) dcm image dataset and (2) relevant structure from the RTSTRUCT.dcm file exported from RayStation
    Note: no date or name information is stored in the metadata of these nifti files, so they are considered fully anonymized.
    HOWEVER, the nifti filename contains the study date by default. I recommend changing this manually retrospectively once
    all desired data has been converted to nifti format (e.g. Fraction1.nii.gz).

### Step 3: Format ultrasound data for export to RayStation
On the Clarity workstation, you need to apply the couch shifts to the ultrasound images so that the ultrasounds are in the same frame of reference as the corresponding CBCT and CT SIM. Instructions for this are on the Desktop of the Clarity Workstation. Once these shifts have been applied and the resulting images saved as 'contouring workspaces', these can be exported to Research Raystation as dicoms. They are not anonymized, so can be linked up with the CT/CBCT data previously imported. Note: the only reason that we need to export to Raystation is so that Clarity will automatically convert the images into the dicom file format with the desired registrations applied. Direct export from Clarity will result ultrasounds saved in the so-called 'usf' file format in which US images are still in polar coordinates in the native frame of reference. Also note: the ultrasounds show up in the RayStation 'data management' tab in the order in which they were exported -- NOT the order in which they were acquired. I advise manually re-naming the images in the RayStation data management tab by date so it's obvious which US corresponds to which CBCT/CT.

### Step 4: Export US data from Raystation to your local machine

The export pipeline should be as follows:
Research Raystation (not anonymized) ==> rtp-bridge (anonymized*) ==> Local machine

*Be sure to tick the 'Anonymization' export box when exporting from Research Raystation, but set the following:
  1. Patient Name: gXX (i.e. g02)
  2. Patient ID: GENIUSII
  3. **Tick 'Retain UIDs'**

Note: there is no date information in the US dicom metadata when exported from Clarity to RayStation. Although it is theoretically possible to sort through a huge dump of US dicom data and determine which individual files correspond to a single 3D image, it is *impossible* to trace back which date/fraction these images came from. 

Therefore, the export process in this step is quite tedious, as each US needs to be exported individually into an appropriately named folder (i.e. US_Jul01) so you can work out which US corresponds to which CBCT/CT. Don't lump US and CBCT/CT data into the same folders.

### Step 5: Convert US dicom data from each individual folder (Local machine) into niftis organized by patient name and date
Upon successfuly export of the US data, you should have many directories; each labelled as 'US_MMMDD' and containing the dicom files corresponding to the date in the directory name. Run the following code for each folder separately (so if you have 20 folders, you'll need to run the following code 20 times). This will convert the dicoms into nifti files and automatically save them in the 'images' sub-directory corresponding to your patient name (see Destination File Structure). 

**Modify sys.path.append line?**

 1. raystationUSdcm_to_nifti.py

  Inputs:

    1. dcm_dir_us: full file path to the directory where the US dicoms have been saved (exported from RayStation)
    e.g. dcm_dir_us = '/Users/sblackledge/Documents/GENIUSII_exports/RayStation/g01/US_July06'
    
    2. save_dir: full file path to the directory where you wish to save the nifti files. 
        i.e. save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01' 


Output:

    1. nii.gz file of CBCT that has been registered/resampled to the CTref. Note: no date or name information is stored in the metadata of these nifti files, so they are considered fully anonymized. HOWEVER, the nifti filename contains the study date by default. I recommend changing this manually retrospectively once all desired data has been converted to nifti format (e.g. Fraction1.nii.gz).

### Step 6: Copy nifti dump folder to storage device
Once you've got all of the data you want to analyse in your nifti_dump folder, you can copy this to the external storage device to be used with the MATLAB app. You can then make the ITK-SNAP workspaces (See Step 7) by loading in the desired nifti files saved on the storage device. 

### Step 7: Generate ITK-SNAP workspaces
An ITK-SNAP workspace is a file that contains information about the so-called 'image layers' (source nifti files) and display settings (transparency, colormaps, default contrast and zoom, etc.) for data loaded into the ITK-SNAP image viewer. In other words, a saving a 'workspace' is like saving a particular 'state' of the viewer once you have loaded all of the required images and adjusted the display settings appropriately. 

For this project, we will have to save all of the workspaces ourselves in advance to ensure consisent and correct loading of images and default display settings. *All workspaces must be saved on the external hard drive in the 'workspaces' folder: /Volumes/SarahB_USB/nifti_dump/workspaces*. The source files that these workspaces reference should also be saved on the external hard drive in the 'nifti_dump' folder (file paths listed below):

1. /Volumes/SarahB_USB/nifti_dump/images
2. /Volumes/SarahB_USB/nifti_dump/masks
  
How to generate a workspace:
  1. Drag the CT SIM image into ITK-snap to 'load as main image'. 
  2. Press ⌘i to open the 'Image Layer Inspector'. Select the 'Contrast' tab, and click 'Auto'.
  3. Drag the CBCT image (if required) into ITK-snap. Select 'Load as Additional Image'. By default, all 'additional' images are loaded as separate thumbnails in the right hand corner of the image viewer, and the observer can toggle back and forth between the two images. This is not what we want. Right click on the CBCT image and click 'Display as Overlay' to superimpose the CBCT on top of the CT SIM.
  4. Go to the 'Contrast' tab on the 'Image Layer Inspector', make sure the CBCT image is highlighted in the left-hand pane by clicking on it, and then select 'Auto' to adjust the default contrast of the CBCT image. 
  5. Repeat steps 7.3 and 7.4 for the US image (if required). 
  6. Set the Opacity of the US image to 0.5 by going to the 'General' tab in the Image Layer Inspector, and typing '50%' in the 'Overlay opacity' textbox.
  7. Load in the masks in the order listed below. The Overlay Opacity should be set to 50% (see step 6), and the visibility should be set to 'off' by clicking the eye icon next to the transparency slider under the structure name in the left-hand pane. The colormap can be set to the specified mask by selecting the 'Color Map' tab in the Image Layer inspector, and selecting the appropriate map in the colormap list.
  
      PTV45_1:	gold mask
      
      PTV45_2:	purple mask
      
      PTV45_3:	pink mask
      
      PTV45_Robust:	blue mask
      
      CTV-T LRinit_1_Full:	green mask
      
      Bladder:	yellow mask
      
      Rectum:	brown mask
      
      CTV-T HRinit: red mask
      
  8. Save the workspace by navigating to Workspace ==> Save workspace as. Label the workspace using the following naming convention:
      (a) gXX_FractionXX_CBCT-US (for workspaces that contain both US and CBCT)
      (b) gXX_FractionXX_CBCT (for workspaces that contain CBCT-only)
      (c) gXX_FractionXX_US (for workspaces that contain US-only). 
      
  **TIP for speeding up subsequent workspaces after the first one for a particular patient has been generated**
  
  Rather than performing steps 7.1 - 7.8 for every single fraction, you can simply remove the daily images (either the CBCT, US, or both) and drag over new ones. In this way, the ref CT and structures will already be loaded into ITK-snap with the correct settings. To remove a daily image from the viewer, right click on the image in the left-hand pane of the Image Layer inspector and click 'Close image "*image name*". Then drag the desired daily image into the ITK-snap image viewer and right click to select 'Display as overlay'. By default, this new daily image will be the last image in the list of additional images in the layer inspector, which will cause display issues when toggling structures on and off. To fix, select the 'General' tab in the Image Layer Inspector, click on the daily image to highlight, and then select the 'Move up' button in the 'Display order' line. Click until your daily image is the first image in the 'Additional Images' category in the left-hand pane. In cases in which both US adn CBCT are available, the CBCT should be the first 'additional image' and the US should be the second. Remember to set the contrast to 'Auto' for the daily images (see step 7.4 above)

