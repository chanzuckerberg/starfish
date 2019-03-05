mkdir -p /tmp/starfish/raw
mkdir -p /tmp/starfish/formatted
mkdir -p /tmp/starfish/registered
mkdir -p /tmp/starfish/filtered
mkdir -p /tmp/starfish/results

python data_formatting_examples/format_iss_data.py /tmp/starfish/raw /tmp/starfish/formatted --d 1

starfish registration \
    -i /tmp/starfish/formatted/primary_images-fov_000.json \
    -o /tmp/starfish/registered/primary_images.json \
    FourierShiftRegistration \
    --reference-stack /tmp/starfish/formatted/nuclei-fov_000.json \
    --upsampling 1000

starfish filter \
    -i /tmp/starfish/registered/primary_images.json \
    -o /tmp/starfish/filtered/primary_images.json \
    WhiteTophat \
    --masking-radius 15

starfish filter \
    -i /tmp/starfish/formatted/nuclei-fov_000.json \
    -o /tmp/starfish/filtered/nuclei.json \
    WhiteTophat \
    --masking-radius 15

starfish filter \
    -i /tmp/starfish/formatted/dots-fov_000.json \
    -o /tmp/starfish/filtered/dots.json \
    WhiteTophat \
    --masking-radius 15

starfish detect_spots \
    --input /tmp/starfish/filtered/primary_images.json \
    --output /tmp/starfish/results/spots.nc \
    --blobs-stack /tmp/starfish/filtered/dots.json \
    BlobDetector \
    --min-sigma 4 \
    --max-sigma 6 \
    --num-sigma 20 \
    --threshold 0.01

starfish segment \
    --primary-images /tmp/starfish/filtered/primary_images.json \
    --nuclei /tmp/starfish/filtered/nuclei.json \
    -o /tmp/starfish/results/label_image.png \
    Watershed \
    --nuclei-threshold .16 \
    --input-threshold .22 \
    --min-distance 57

starfish target_assignment \
    --label-image /tmp/starfish/results/label_image.png \
    --intensities /tmp/starfish/results/spots.nc \
    --output /tmp/starfish/results/targeted-spots.nc \
    Label

starfish decode \
    -i /tmp/starfish/results/targeted-spots.nc \
    --codebook /tmp/starfish/formatted/codebook.json \
    -o /tmp/starfish/results/decoded-spots.nc \
    PerRoundMaxChannelDecoder

