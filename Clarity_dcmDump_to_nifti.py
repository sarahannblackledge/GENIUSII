import os
import numpy as np
import SimpleITK as sitk
import pydicom as dicom
import sys
sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from copy_dicom_tags import copy_dicom_tags
from create_rtstruct_mask_SB import create_rtstruct_masks

'''Organizes CT and CBCT images contained in DICOMRawData based on Series Instance UID. 
Saves as nifti files to user-specified directory.

Note: The DICOMRawData folder created as part of the Clarity Export Patient function does not contain any ultrasound 
data, as these are not inherently in DICOM format.

Inputs:
    1. ct_directory: str - full filepath where DICOMRawData folder is stored. This contains a dump of 
    all CBCT and CT dicoms exported from the Clarity system, and is not organized in an intuitive way.
    Example: ct_directory =  '/Users/sblackledge/Documents/GENIUSIII_exports/Clarity/g01/DICOMRawData
    2. save_dir: str - full filepath where nifti files should be saved. 
    Example: save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images'
    3. patient_name: str - string indicating name of patient. Example: 'g01'
    
Output:
    Nifti file for every dcm image dataset contained in DICOMRawData.
'''

def DICOMRawData_to_nifti(ct_directory, save_dir, patient_name):
    study_uids_blacklist = {}
    floc_el = 0x19100c #Used to store the file location in read dicoms

    #Create 'images' sub-directory.
    im_dir = os.path.join(save_dir, 'images', patient_name)
    CHECK_FOLDER = os.path.isdir(im_dir)
    if not CHECK_FOLDER:
        os.makedirs(im_dir)

    #Create 'masks' sub-directory
    mask_dir = os.path.join(save_dir, 'masks', patient_name)
    CHECK_FOLDER = os.path.isdir(mask_dir)
    if not CHECK_FOLDER:
        os.makedirs(mask_dir)

    # Load in the ct dicoms and RTSTRUCT dicoms as separate lists
    ct_dicoms = {}
    rtstruct_dicoms = []
    for dicom_file in os.listdir(ct_directory):
        if dicom_file == ".DS_Store":
            continue

        try:
            dicom_path = os.path.join(ct_directory, dicom_file)
            dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
            series_uid = dcm.SeriesInstanceUID
            modality = dcm.Modality
            if dcm.StudyInstanceUID in study_uids_blacklist.keys():
                break

            #Both CT and CBCT labeled with modality 'CT'
            if modality == 'CT':
                if not series_uid in ct_dicoms:
                    ct_dicoms[series_uid] = []
                dcm.add_new(floc_el, "ST", dicom_path)
                ct_dicoms[series_uid].append(dcm)

            if modality == 'RTSTRUCT':
                rtstruct_dcm = dicom.read_file(dicom_path, stop_before_pixels=True)
                rtstruct_dcm.add_new(floc_el, "ST", dicom_path)
                rtstruct_dicoms.append(rtstruct_dcm)

            #Use RTPLAN to identify approved RTSTRUCT uid
            if modality == 'RTPLAN':
                plan_series_uid = series_uid
                ref_rtstruct_uid = dcm[0x300c, 0x0060][0][0x0008, 0x1155].value
                ref_rtstruct_uid_str = str(ref_rtstruct_uid)
        except:
            raise

    # Now organise files in CT lists by ascending slice location
    for series_uid in ct_dicoms:
        slice_locations = [float(dcm.ImagePositionPatient[-1]) for dcm in ct_dicoms[series_uid]]
        ct_dicoms[series_uid] = np.array(ct_dicoms[series_uid])[np.argsort(slice_locations)].tolist()

    # Read in approved RTSTRUCT dicom corresponding to RTPLAN file.
    for rtstruct in rtstruct_dicoms:
        if rtstruct.SOPInstanceUID == ref_rtstruct_uid:
            ref_rtstruct = rtstruct
            if ref_rtstruct is None:
                print("Could not find a rtstruct for plan: %s" % str(plan_series_uid))
                continue

    # Find the CT image corresponding to the RTSTRUCT
    ref_ct_series_uid = ref_rtstruct[0x3006, 0x10][0][0x3006, 0x12][0][0x3006, 0x14][0][0x20, 0xe].value
    for series_uid in ct_dicoms:
        if series_uid == ref_ct_series_uid:
            ref_ct_study = ct_dicoms[series_uid]
            ref_ct_image = sitk.ReadImage([dcm[floc_el].value for dcm in ref_ct_study]) #sitk object for ref CT
            if ref_ct_study is None:
                print("Could not find a CT series corresponding to RTSTRUCT: %s" % str(ref_rtstruct_uid))
                continue

    #Convert each CT in ct_dicoms list to nifti file. Save to location specified by save_dir
    for series_id in ct_dicoms:
        ref_ct_study = ct_dicoms[series_id]

        #Generate sitk object
        ct_image = sitk.ReadImage([dcm[floc_el].value for dcm in ref_ct_study])
        copy_dicom_tags(ct_image, ref_ct_study[0], ignore_private=True)

        #Get date and series description from metadata - to be used in filename of nifti file
        study_date = ct_image.GetMetaData('0008,0020') #Date
        month = str(study_date[4:6])
        day = str(study_date[-2:])
        series_description = ct_image.GetMetaData('0008,103e')

        month_dict = {
            "01": "Jan",
            "02": "Feb",
            "03": "Mar",
            "04": "Apr",
            "05": "May",
            "06": "Jun",
            "07": "Jul",
            "08": "Aug",
            "09": "Sep",
            "10": "Oct",
            "11": "Nov",
            "12": "Dec"
        }

        month_name = month_dict[month]
        date_name = month_name + day + '.nii.gz'
        if 'CBCT' in series_description:
            fname = 'CBCT' + '_' + date_name
        else:
            fname = 'CT' + '_' + date_name

        #Save CTs to images sub-directory in 'nifti dump' folder
        save_path = os.path.join(im_dir, fname)
        sitk.WriteImage(ct_image, save_path, True)

    #Generate masks of each structure in RTSTRUCT.
    rtstruct_images_sub = create_rtstruct_masks(ref_rtstruct, ref_ct_image) #output: list of sitk objects

    for im in rtstruct_images_sub:
        structure_name = im.GetMetaData("ContourName") + '.nii.gz'
        fpath_structure = os.path.join(mask_dir, structure_name)
        sitk.WriteImage(im, fpath_structure, True)

    return ct_dicoms, ref_ct_image, rtstruct_images_sub

patient_name = 'g01'
ct_directory = '/Users/sblackledge/Documents/GENIUSII_exports/Clarity/g01/DICOMRawData'
save_dir = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump'
ct_dicoms, ct_example, rtstruct_sitk = DICOMRawData_to_nifti(ct_directory, save_dir, patient_name)

