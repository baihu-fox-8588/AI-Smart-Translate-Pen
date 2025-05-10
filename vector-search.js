const { Plugin } = require('obsidian');

class VectorSearchPlugin extends Plugin {
    async onload() {
        this.addCommand({
            id: 'vector-search',
            name: 'Vector Search',
            callback: () => this.showSearchModal()
        });
    }

    async showSearchModal() {
        const modal = new SearchModal(this.app, this);
        modal.open();
    }

    async searchSimilarNotes(query) {
        const files = this.app.vault.getMarkdownFiles();
        const queryVector = await this.getEmbedding(query);
        const results = [];

        for (const file of files) {
            const content = await this.app.vault.read(file);
            const frontmatter = this.app.metadataCache.getFileCache(file)?.frontmatter;
            
            if (frontmatter?.vector) {
                const similarity = this.cosineSimilarity(
                    queryVector,
                    JSON.parse(frontmatter.vector)
                );
                
                if (similarity > 0.7) { // 相似度閾值
                    results.push({
                        file,
                        similarity
                    });
                }
            }
        }

        return results.sort((a, b) => b.similarity - a.similarity);
    }

    async getEmbedding(text) {
        // 這裡需要實現與 Gemini API 的連接
        // 為了示範，我們返回一個隨機向量
        return Array(768).fill(0).map(() => Math.random());
    }

    cosineSimilarity(vecA, vecB) {
        const dotProduct = vecA.reduce((sum, a, i) => sum + a * vecB[i], 0);
        const normA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
        const normB = Math.sqrt(vecB.reduce((sum, b) => sum + b * b, 0));
        return dotProduct / (normA * normB);
    }
}

class SearchModal extends Modal {
    constructor(app, plugin) {
        super(app);
        this.plugin = plugin;
    }

    onOpen() {
        const { contentEl } = this;
        contentEl.createEl('h2', { text: 'Vector Search' });
        
        const input = contentEl.createEl('input', {
            type: 'text',
            placeholder: 'Enter your search query...'
        });

        const resultsDiv = contentEl.createEl('div', {
            cls: 'search-results'
        });

        input.addEventListener('input', async (e) => {
            const query = e.target.value;
            if (query.length > 2) {
                const results = await this.plugin.searchSimilarNotes(query);
                this.displayResults(results, resultsDiv);
            }
        });
    }

    displayResults(results, container) {
        container.empty();
        results.forEach(result => {
            const resultEl = container.createEl('div', {
                cls: 'search-result'
            });
            resultEl.createEl('div', {
                text: `${result.file.basename} (${(result.similarity * 100).toFixed(1)}% similar)`
            });
            resultEl.addEventListener('click', () => {
                this.app.workspace.getLeaf().openFile(result.file);
                this.close();
            });
        });
    }

    onClose() {
        const { contentEl } = this;
        contentEl.empty();
    }
}

module.exports = VectorSearchPlugin; 