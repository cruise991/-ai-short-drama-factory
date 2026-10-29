import json

file_path = "assets/dance/01_characters/ips/C006_Yumi.json"
with open(file_path, "r") as f:
    data = json.load(f)

# Double check the string replacement worked properly
data["skin"] = "flawless glass glowing skin, ultra-detailed skin texture, realistic pores, fair skin, perfectly even skin tone without extreme blush"
data["anchor_prompt"] = data["anchor_prompt"].replace("fair skin with slight natural blush", "fair skin, perfectly even skin tone without extreme blush")
data["anchor_prompt"] = data["anchor_prompt"].replace("glass glowing skin", "flawless glass glowing skin").replace("perfectly even skin tone, ", "perfectly even skin tone without extreme blush, ")
# Clean up duplicate just in case
data["anchor_prompt"] = data["anchor_prompt"].replace("without extreme blush without extreme blush", "without extreme blush")

with open(file_path, "w") as f:
    json.dump(data, f, indent=2)

file_path_lili = "assets/dance/01_characters/ips/C005_Lili.json"
with open(file_path_lili, "r") as f:
    data_lili = json.load(f)

data_lili["skin"] = "flawless glass glowing skin, ultra-detailed skin texture, realistic pores, fair skin, perfectly even skin tone without extreme blush"
data_lili["anchor_prompt"] = data_lili["anchor_prompt"].replace("fair skin with slight natural blush", "fair skin, perfectly even skin tone without extreme blush")
data_lili["anchor_prompt"] = data_lili["anchor_prompt"].replace("glass glowing skin", "flawless glass glowing skin").replace("perfectly even skin tone, ", "perfectly even skin tone without extreme blush, ")
data_lili["anchor_prompt"] = data_lili["anchor_prompt"].replace("without extreme blush without extreme blush", "without extreme blush")

with open(file_path_lili, "w") as f:
    json.dump(data_lili, f, indent=2)
print("Done fixing ips.")
