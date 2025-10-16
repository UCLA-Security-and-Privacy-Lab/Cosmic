#!/bin/bash
while getopts c: flag
do
    case "${flag}" in
        c) config=${OPTARG};;
    esac
done

source /u/fr3ya/miniforge3/etc/profile.d/conda.sh
conda activate webnav
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH

export OPENAI_API_KEY=sk-proj-xxxxxx

config_folder="/bigtemp/fr3ya/webarena/configure/${config}"
result_folder="/bigtemp/fr3ya/webarena/results_test/${config}"
facts_folder="/bigtemp/fr3ya/webarena/compliance_check/code/test_data/${config}"

echo $config_folder

# mkdir -p $facts_folder


timeout 1800s python run.py --instruction_path agent/prompts/jsons/p_cot_id_actree_2s.json --test_start_idx 0 --test_end_idx 1 --config_folder $config_folder --model gpt-4o-mini --result_dir $result_folder

# python ./pipeline_integration/scripts/select_same_page_structure.py --folder $result_folder 
# If need to run for all directories, run `python ./pipeline_integration/scripts/overall_pkl_select.py`
# python ./pipeline_integration/scripts/select_iframes.py --folder $result_folder

# python pipeline_integration/form_operation_scripts/save_image.py
# source /home/ying/anaconda3/bin/activate py310

# mkdir -p $result_folder/segmented_images

# # Screenshot Segmentation
# python ./scripts/image_process/segment.py --input_folder $result_folder/images
# python ./scripts/image_process/webpage_screenshot_analyzer.py --input_folder $result_folder/segmented_images

# python pipeline_integration/form_operation_scripts/multimodal_form_extraction.py $result_folder #modify this file

# # cd /home/ying/projects/web_navigation/webarena/pipeline_integration/scripts
# python /home/ying/projects/web_navigation/webarena/pipeline_integration/scripts/form_property.py --folder $result_folder




# python /home/ying/projects/web_navigation/consent_management/compliance_check/scripts/facts_extraction.py --result_folder $result_folder --facts_folder $facts_folder

# facts_folder_new=$(find $facts_folder -type d | awk '{print length, $0}' | sort -n | tail -1 | cut -d" " -f2-)
# # cd /home/ying/projects/web_navigation/consent_management/crt_identification/scripts

# python /home/ying/projects/web_navigation/consent_management/crt_identification/scripts/checkbox_crt.py $facts_folder_new

# python /home/ying/projects/web_navigation/consent_management/compliance_check/scripts/get_purpose.py --facts_save_dir $facts_folder_new

# python '/home/ying/projects/web_navigation/consent_management/compliance_check/scripts/get_suboperation.py' --facts_save_dir $facts_folder_new

# python /home/ying/projects/web_navigation/consent_management/compliance_check/scripts/text_similarity_measure.py --facts_save_dir $facts_folder_new

# touch $facts_folder_new/collect.facts
# touch $facts_folder_new/subsume.facts
# mkdir -p $facts_folder/output
# cd /home/ying/projects/web_navigation/consent_management/compliance_check/code/violation_reasoning
# souffle -F $facts_folder_new -D $facts_folder/output violation_rules.datalog