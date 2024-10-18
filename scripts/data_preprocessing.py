import os
import numpy as np
from PIL import Image, UnidentifiedImageError
from sklearn.model_selection import train_test_split
from tqdm import tqdm

class ISICDataset:
    def __init__(self, imgs_dir, masks_dir, batch_size=32, target_size=(224, 224)):
        self.imgs_dir = imgs_dir
        self.masks_dir = masks_dir
        self.batch_size = batch_size
        self.target_size = target_size
        self.valid_image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')  # Extensions d'images valides

        # Ne pas charger toutes les images en mémoire, on les traite par lot.
        self.img_files = sorted([f for f in os.listdir(self.imgs_dir) if f.lower().endswith(self.valid_image_extensions)])
        self.mask_files = sorted([f for f in os.listdir(self.masks_dir) if f.lower().endswith(self.valid_image_extensions)])

        # Vérification que les fichiers images et masques correspondent en nombre
        assert len(self.img_files) == len(self.mask_files), "Nombre d'images et de masques ne correspondent pas"

    def __len__(self):
        return len(self.img_files) // self.batch_size

    def __getitem__(self, idx):
        # Charger un batch d'images et de masques
        batch_img_files = self.img_files[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_mask_files = self.mask_files[idx * self.batch_size:(idx + 1) * self.batch_size]
        
        images = []
        masks = []

        for img_file, mask_file in zip(batch_img_files, batch_mask_files):
            img_path = os.path.join(self.imgs_dir, img_file)
            mask_path = os.path.join(self.masks_dir, mask_file)

            try:
                img = Image.open(img_path).convert('RGB')  # Lire et convertir l'image
                img = img.resize(self.target_size)  # Redimensionner l'image pour optimiser l'usage de la mémoire
                mask = Image.open(mask_path).convert('L')  # Lire et convertir le masque en niveaux de gris
                mask = mask.resize(self.target_size)  # Redimensionner le masque
            except UnidentifiedImageError:
                print(f"Skipping non-image file: {img_path} or {mask_path}")
                continue

            images.append(np.array(img))
            masks.append(np.array(mask))

        return np.array(images), np.array(masks)

    def split_data(self):
        # Diviser les données par indices pour éviter de charger en mémoire toutes les images
        indices = np.arange(len(self.img_files))
        train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42)
        val_idx, test_idx = train_test_split(test_idx, test_size=0.5, random_state=42)

        return train_idx, val_idx, test_idx

def save_preprocessed_data(dataset, output_dir, split, idx_list):
    img_dir = os.path.join(output_dir, split, 'images')
    mask_dir = os.path.join(output_dir, split, 'masks')
    
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)

    for idx in tqdm(idx_list, desc=f"Stockage {split} données"):
        images, masks = dataset[idx]

        for i in range(len(images)):
            img = Image.fromarray(images[i])
            mask = Image.fromarray(masks[i])
            img.save(os.path.join(img_dir, f'image_{idx * dataset.batch_size + i}.png'))
            mask.save(os.path.join(mask_dir, f'mask_{idx * dataset.batch_size + i}.png'))
