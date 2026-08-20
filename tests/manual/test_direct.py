import sys
import os
import importlib.util

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
_de_path = os.path.join("departments", "02_planning", "director_engine.py")
_de_spec  = importlib.util.spec_from_file_location("director_engine", _de_path)
_de_mod   = importlib.util.module_from_spec(_de_spec)
_de_spec.loader.exec_module(_de_mod)

result = _de_mod.direct('C004_Nyx', 30, None, module_params={'vibe': 'energy'}, custom_beats=[12, 18])
types = [s['type'] for s in result['stage_2_video']['timeline']]
assert 'hook' in types and 'dance' in types and 'pose' in types, f'Missing type: {types}'
print('✅ 3-type check passed:', types)
print('✅ Vibe:', result['metadata']['vibe'])
print('✅ Camera:', result['stage_2_video']['camera_control'])
