from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D

# Parole da visualizzare
words = ["re", "uomo", "donna", "regina"]

# Carica il modello e crea gli embedding
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
embeddings = model.encode(words)

# PCA per ridurre a 3 dimensioni
pca = PCA(n_components=3)
emb3d = pca.fit_transform(embeddings)

# Crea figura 3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Colori per genere (maschile: blu, femminile: rosso)
colors = {'uomo': 'blue', 're': 'blue', 'donna': 'red', 'regina': 'red'}

# Plot con proiezioni
for word, (x, y, z) in zip(words, emb3d):
    ax.scatter(x, y, z, color=colors[word], s=50)
    ax.text(x, y, z, f" {word}", fontsize=12)

    # Proiezione su piano XY (z = min_z)
    ax.scatter(x, y, min(emb3d[:, 2]) - 0.05, color=colors[word], alpha=0.3, marker='o', s=30)
    ax.plot([x, x], [y, y], [z, min(emb3d[:, 2]) - 0.05], color=colors[word], alpha=0.3)

    # Proiezione su piano XZ (y = min_y)
    ax.scatter(x, min(emb3d[:, 1]) - 0.05, z, color=colors[word], alpha=0.3, marker='o', s=30)
    ax.plot([x, x], [y, min(emb3d[:, 1]) - 0.05], [z, z], color=colors[word], alpha=0.3)

    # Proiezione su piano YZ (x = min_x)
    ax.scatter(min(emb3d[:, 0]) - 0.05, y, z, color=colors[word], alpha=0.3, marker='o', s=30)
    ax.plot([x, min(emb3d[:, 0]) - 0.05], [y, y], [z, z], color=colors[word], alpha=0.3)

# Etichette assi
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_zlabel("PC3")
ax.set_title("Embedding 3D con proiezioni sui piani")

# Impostazioni dei limiti per visualizzare bene i piani
ax.set_xlim(min(emb3d[:, 0]) - 0.1, max(emb3d[:, 0]) + 0.1)
ax.set_ylim(min(emb3d[:, 1]) - 0.1, max(emb3d[:, 1]) + 0.1)
ax.set_zlim(min(emb3d[:, 2]) - 0.2, max(emb3d[:, 2]) + 0.1)

plt.tight_layout()
plt.show()

