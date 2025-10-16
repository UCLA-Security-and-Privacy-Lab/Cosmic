## Quick Start

1. Run for one website 

Before start, please configure a website, together with the prompt in the configure. Configuratin file is under folder `config`


```bash
export OPENAI_API_KEY = "your api key"
python run.py --instruction_path agent/prompts/jsons/p_cot_id_actree_2s.json --test_start_idx 0 --test_end_idx 1  --model gpt-4o-mini --result_dir ./results/
```
For batch run, you can try `batch_run.py`

2. Saved Traces
   
The saved traces is under folder `./results/trajectory_x.json.pkl`

To read the original data saved in pkl
```python
import pickle 
with open(xxx, 'rb') as f:
    trace = pickle.load(f)
```
The trace format is `Trajectory = list[Union[StateInfo, Action]]`, so the even indexed (0,2,4..) are StateInfo, odd indexed are Actions.

The `StateInfo` Item includes all information you need:
    - observation
      - text (simplified Accessibility Tree)
      - image (stored in array, you can transform to screenshot when needed)
    - info
      - page
        - content (source HTML of this page)
        - url
      - obs
      - observation_metadata
      - iframe (because sometimes the form might be in iframe code, which cannot be get from the website source code)
      - ...

3. If you want to add your proxy, please add in `browser_env/envs.py` `setup` function.

More scripts details please see under `pipeline_integration`