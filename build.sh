#!/bin/bash
# Build and deploy script for Z-Image Turbo RunPod endpoint

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Z-Image Turbo Build & Deploy${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check for required commands
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is not installed${NC}" >&2; exit 1; }

# Get Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USER
if [ -z "$DOCKER_USER" ]; then
    echo -e "${RED}Error: Docker Hub username is required${NC}"
    exit 1
fi

# Image name
IMAGE_NAME="${DOCKER_USER}/z-image-turbo"
VERSION="latest"
FULL_IMAGE="${IMAGE_NAME}:${VERSION}"

echo ""
echo -e "${YELLOW}Building Docker image: ${FULL_IMAGE}${NC}"
echo ""

# Build
docker build -t "${FULL_IMAGE}" .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo ""
    
    # Ask if user wants to push
    read -p "Push to Docker Hub? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
        docker push "${FULL_IMAGE}"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Successfully pushed to Docker Hub!${NC}"
            echo ""
            echo -e "${GREEN}================================${NC}"
            echo -e "${GREEN}Next Steps:${NC}"
            echo -e "${GREEN}================================${NC}"
            echo ""
            echo "1. Go to RunPod Console: https://runpod.io"
            echo "2. Create a Network Volume:"
            echo "   - Name: z-image-models"
            echo "   - Size: 15 GB"
            echo ""
            echo "3. Create Serverless Endpoint:"
            echo "   - Image: ${FULL_IMAGE}"
            echo "   - GPU: 48GB (A6000, L40, L40S)"
            echo "   - Container Disk: 20GB"
            echo "   - Network Volume: z-image-models at /runpod-volume"
            echo "   - Workers: Min 0, Max 1-3"
            echo "   - Enable FlashBoot"
            echo ""
            echo "4. Test your endpoint:"
            echo "   export RUNPOD_API_KEY=your_key"
            echo "   export RUNPOD_ENDPOINT_ID=your_endpoint_id"
            echo "   python tests/test_handler.py"
            echo ""
        else
            echo -e "${RED}✗ Push failed${NC}"
            exit 1
        fi
    else
        echo ""
        echo -e "${YELLOW}Skipped push. You can push later with:${NC}"
        echo "docker push ${FULL_IMAGE}"
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
