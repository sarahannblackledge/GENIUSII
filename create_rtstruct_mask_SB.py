import SimpleITK as sitk
import numpy as np
from skimage.draw import polygon
import sys
from tqdm import tqdm
import copy
sys.path.append('/Users/sblackledge/PycharmProjects/pythonProject/GENIUSII')
from get_python_tags import get_dicom_tags


def create_rtstruct_masks(rtstruct_dicom, ct_image):
    """ Convert rtstruct dicom file to sitk images

    Args
    ====
    fpath_rtstruct : full file path to RTSTRUCT.dcm file

    ct_image : SimpleITK.Image
    The CT image on which the RTStruct is defined.

    save_dir : full file path to directory where masks should be saved

    Return
    ======
    masks : list
    A list of SimpleITK.Image instances for the masks

    """
    # Provides the names
    #0x30060022 = ROI Number
    #0x30060026 = ROI Name
    structure_sets = {int(d[0x30060022].value):d for d in rtstruct_dicom[0x30060020]}

    masks_of_interest = ['Bladder', 'PTV45_1', 'PTV45_2', 'PTV45_3', 'PTV45_Robust', 'Rectum', 'CTV-E', 'CTV-T HRinit', 'CTV-T LRinit_1_Full']
    # masks_of_interest = ['Rectum', 'Bowel', 'Bladder', 'Penile_Bulb', 'ProstateOnly', 'SVsOnly', 'CTV_Prostate', 'CTV_SVs', 'CTV_Prostate+SVs', 'PTV_4860']
    #masks_of_interest = ['ProstateOnly', 'SVsOnly', 'Rectum', 'Bladder', 'Bowel']

    orX, orY, orZ = ct_image.GetOrigin()
    szX, szY, szZ = ct_image.GetSize()
    spX, spY, spZ = ct_image.GetSpacing()
    z_locs = orZ + np.arange(szZ) * spZ

    masks = []
    names = {}

    mask_idx = 0
    contour_sequences = rtstruct_dicom.ROIContourSequence

    # For each contour itemized in ROIContourSequence tag
    for item in contour_sequences:
        roi_mask = np.zeros(ct_image.GetSize(), dtype="int")
        contourSequence = item.ContourSequence
        structure_idx = item[0x30060084].value
        contour_name = structure_sets[structure_idx][0x30060026].value

        if contour_name in masks_of_interest:
            names[mask_idx] = contour_name
            print(contour_name)

            #For each slice comprising stucture
            for j in contourSequence:
                xyz = j.ContourData
                x = xyz[0::3]
                y = xyz[1::3]
                z = xyz[2::3]
                z_diff = np.abs(z_locs - z[0])
                z_idx = np.where(z_diff == np.min(z_diff))[0][0]
                x_arr  =np.asarray(x)
                y_arr = np.asarray(y)
                x = (x_arr - orX) / spX
                y = (y_arr - orY) / spY
                mask = roi_mask[:, :, z_idx]
                mask_new = np.zeros_like(mask)
                rr, cc = polygon(x, y, mask.shape)
                mask_new[rr, cc] = True
                mask = np.logical_xor(mask, mask_new)
                roi_mask[:, :, z_idx] = mask

            masks.append(roi_mask)
            mask_idx += 1


    masks = np.array(masks).transpose((3, 2, 1, 0))
    mask_images = []
    tags = get_dicom_tags(rtstruct_dicom, ignore_private=True, ignore_groups=[0x3006])
    name_idx_dict = dict((v, k) for k, v in names.items())

    #generate sitk image for each mask and concatenate into single array
    for idx in tqdm(names, leave=False, desc="Creating individual"):
        #print(idx)
        mask_image_sub = sitk.GetImageFromArray(masks[:, :, :, idx].astype("uint8"))
        mask_image_sub.CopyInformation(ct_image)
        mask_image_sub.SetMetaData("ContourName", names[idx])
        ref_ct_series_uid = rtstruct_dicom[0x3006, 0x10][0][0x3006, 0x12][0][0x3006, 0x14][0][0x20, 0xe].value
        mask_image_sub.SetMetaData("CTSeriesUID", ref_ct_series_uid)
        for key in tags:
            mask_image_sub.SetMetaData(key, tags[key])
        if names[idx] in masks_of_interest:
            mask_images.append(mask_image_sub)
        #If a bowel contour does not exist, create one, but filled with zeros.

    return mask_images




