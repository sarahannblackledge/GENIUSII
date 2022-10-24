import numpy as np
import os
import SimpleITK as sitk
import matplotlib.pyplot as plt
import copy



def create_im_list(*args):
    sitk_ims = []
    for i in args:
        print(i)
        sitk_im = sitk.ReadImage(i)
        sitk_ims.append(sitk_im)
    return sitk_ims

'''Extract im size, position, and spacing params'''
def extract_metadata(sitk_im):
    im_origin = np.asarray(sitk_im.GetOrigin())
    im_size = np.asarray(sitk_im.GetSize())
    im_spacing = sitk_im.GetSpacing()
    im_direction = sitk_im.GetDirection()
    pixel_type = sitk_im.GetPixelIDTypeAsString()
    return im_origin, im_size, im_spacing, im_direction, pixel_type

'''Resample individual images onto common (large) reference grid. Also pre-process to crop LR edges to remove
weird edge effect.

    Inputs:
        1. sitk_ims: list of sitk image objects; oubput from create_im_list
    Outputs:
        1. resampled_ims: list of sitk image objects resampeld to common reference grid'''
def format_individual_ims(sitk_ims):
    for i, im in enumerate(sitk_ims):
        if i==0:
            im_origin0, im_size0, im_spacing0, im_direction0, pixel_type = extract_metadata(im)
        else:
            im_origin, im_size, im_spacing, im_direction, pixel_type = extract_metadata(im)
            im_origin0 = np.vstack((im_origin0, im_origin))
            im_size0 = np.vstack((im_size0, im_size))

    #Determine position (mm) of last pixel in xyz for compound image
    last_x = np.amax(im_origin0[:, 0] + (im_size0[:, 0]*im_spacing[0]))
    last_y = np.amax(im_origin0[:,1] + (im_size0[:, 1] * im_spacing[1]))
    last_z = np.amax(im_origin0[:,2] + (im_size0[:, 2] * im_spacing[2]))

    #Determine position (mm) of origin in compound image
    new_origin = np.amin(im_origin0, axis=0)

    #Determine new image size (pixels)
    last_vals = np.array([last_x, last_y, last_z])
    new_size = np.ceil((last_vals - new_origin)/im_spacing)
    new_size = new_size.astype(int)
    new_size = new_size.tolist() #convert from int64 to int

    #Create new sitk image object with size of compound image
    compound_3D_template = sitk.Image(new_size[0], new_size[1], new_size[2], sitk.sitkInt16)
    compound_3D_template.SetOrigin((new_origin[0], new_origin[1], new_origin[2]))
    compound_3D_template.SetSpacing((im_spacing[0], im_spacing[1], im_spacing[2]))

    #Resample original images onto new new compound template. Store in list
    resampled_ims = []
    cutoff = 5
    counter = 0
    for im in sitk_ims:
        counter = counter + 1
        print(counter)
        im_resampled = sitk.Resample(im, compound_3D_template, sitk.AffineTransform(3), sitk.sitkLinear, -1000, sitk.sitkFloat32)
        #Convert all background pixels (-1000) to NaN (note: converts any pixels that's -1000 into NaN even if within US)
        im_resampled_array = sitk.GetArrayFromImage(im_resampled)
        im_resampled_array[im_resampled_array == -1000] = np.NaN

        #Chop off edge pixels to remove weird border effect
        TF = np.isnan(im_resampled_array)
        im_size = TF.shape
        for k in range(im_size[0]):
            slice = TF[k, :, :]
            for i in range(im_size[1]):
                row = slice[i, :]
                int_inds = np.where(~row)[0]
                if int_inds.size > 0: #If array is not empty
                    first_ind = int_inds[0]
                    last_ind = int_inds[-1]
                    new_first_ind = first_ind + cutoff
                    new_last_ind = last_ind - cutoff
                    new_row = row
                    im_resampled_array[k, i, first_ind:new_first_ind] = np.NaN
                    im_resampled_array[k, i, new_last_ind:last_ind+1] = np.NaN

        im_resampled2 = sitk.GetImageFromArray(im_resampled_array)
        im_resampled2.CopyInformation(im_resampled)

        resampled_ims.append(im_resampled2)

    return resampled_ims

'''inputs:
    1. resampled_ims: list of all sitk image objects available
    2. indices: list of indices of resampled_ims to include in compound (i.e. [0, 1])'''
def compound_calculate(resampled_ims, indices):
    array_list = []

    for ind in indices:
        im_sitk = resampled_ims[ind]
        im_array = sitk.GetArrayFromImage(im_sitk)
        array_list.append(im_array)

    im_arrays = np.stack(array_list, axis=3)

    #Compute compound as mean of individual US images
    av_im = np.nanmean(im_arrays, axis=3)
    av_im = np.nan_to_num(av_im, nan=-1000)

    #Convert to sitk image object
    av_im_sitk = sitk.GetImageFromArray(av_im)
    av_im_sitk.CopyInformation(im_sitk)
    return av_im_sitk


'''Modify Code below to make desired compounds'''
#Full pathnames of every image to be considered in the compound. Will be placed in list in the order in which they are
#input to the function 'create_im_list'
fpath1 = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01/US_Jun17_1120.nii.gz'
fpath2 = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01/US_Jun17_1121_1.nii.gz'
fpath3 = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/images/g01/US_Jun17_1121_2.nii.gz'
fpath4 = ''


sitk_ims = create_im_list(fpath1, fpath2, fpath3)

#Directory where compound image nifti files should be saved
dir_compounds = '/Users/sblackledge/Documents/GENIUSII_exports/nifti_dump/compound_images'

#Indices of image list to include in compound
indices = [0, 1, 2]

#Generate compound image
resampled_ims = format_individual_ims(sitk_ims)
compound_im = compound_calculate(resampled_ims, indices)
compound_name = 'June17_compound.nii.gz' #Don't forget to include file extension in name (.nii.gz)
patient_id = 'g01'

'''End Code modification'''

# Create patient sub-directory within dir_compounds directory.
im_dir = os.path.join(dir_compounds, patient_id)
CHECK_FOLDER = os.path.isdir(im_dir)
if not CHECK_FOLDER:
    os.makedirs(im_dir)

#Save compound as nifti
savename = os.path.join(im_dir, compound_name)
sitk.WriteImage(compound_im, savename, True)


