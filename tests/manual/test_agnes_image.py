import sys, os, importlib.util
sys.path.append('.')
if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location('production_agent', 'departments/03_production/production_agent.py')
    pa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pa)
    config = {"PRODUCTION_IMAGE_MODEL": "agnes-image-2.1-flash"}
    pa.generate_image_agnes("Wide angle full body", "test.png", config, "768x1344")
