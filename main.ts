import { App, Modal, Plugin, PluginSettingTab, Setting, TFile, Notice, ItemView, WorkspaceLeaf } from 'obsidian';
import { GoogleGenAI } from "@google/genai";

interface VectorData {
    path: string;        // 檔案路徑
    filename: string;    // 檔案名稱
    vector: number[];    // 向量資料
}

interface VectorSearchSettings {
    similarityThreshold: number;
    apiKey: string;
}

const DEFAULT_SETTINGS: VectorSearchSettings = {
    similarityThreshold: 0.3,
    apiKey: "AIzaSyA0UjnY2qljOsi5SXBhx98s3vQrmITyVgE"
}

export const VECTOR_SEARCH_VIEW_TYPE = 'vector-search-view';

export class VectorSearchView extends ItemView {
    plugin: VectorSearchPlugin;

    constructor(leaf: WorkspaceLeaf, plugin: VectorSearchPlugin) {
        super(leaf);
        this.plugin = plugin;
    }

    getViewType(): string {
        return VECTOR_SEARCH_VIEW_TYPE;
    }

    getDisplayText(): string {
        return '向量搜尋';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        container.addClass('vector-search-view');

        const searchContainer = container.createEl('div', {
            cls: 'search-container'
        });

        const input = searchContainer.createEl('input', {
            type: 'text',
            placeholder: '輸入搜尋內容並按 Enter...'
        });

        const searchButton = searchContainer.createEl('button', {
            text: '搜尋'
        });

        const reloadButton = searchContainer.createEl('button', {
            text: '重新載入',
            cls: 'reload-button'
        });

        const resultsDiv = container.createEl('div', {
            cls: 'search-results'
        });

        const performSearch = async () => {
            const query = input.value;
            if (query.length > 0) {
                resultsDiv.empty();
                const loadingEl = resultsDiv.createEl('div', {
                    text: '搜尋中...'
                });
                const results = await this.plugin.searchSimilarNotes(query);
                resultsDiv.empty();
                this.displayResults(results, resultsDiv);
            }
        };

        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                await performSearch();
            }
        });

        searchButton.addEventListener('click', performSearch);

        reloadButton.addEventListener('click', async () => {
            await this.plugin.loadVectorData();
            new Notice('向量資料已重新載入');
        });
    }

    displayResults(results: { path: string; filename: string; similarity: number }[], container: HTMLElement) {
        container.empty();
        if (results.length === 0) {
            container.createEl('div', {
                text: '沒有找到相似的筆記'
            });
            return;
        }

        results.forEach(result => {
            const resultEl = container.createEl('div', {
                cls: 'search-result'
            });
            
            const titleEl = resultEl.createEl('div', {
                cls: 'result-title',
                text: result.filename
            });
            
            const pathEl = resultEl.createEl('div', {
                cls: 'result-path',
                text: result.path
            });
            
            resultEl.createEl('div', {
                cls: 'similarity',
                text: `${(result.similarity * 100).toFixed(1)}% 相似`
            });

            resultEl.addEventListener('click', async () => {
                const file = this.app.vault.getAbstractFileByPath(result.path);
                if (file && file instanceof TFile) {
                    await this.app.workspace.getLeaf().openFile(file);
                }
            });
        });
    }
}

export default class VectorSearchPlugin extends Plugin {
    settings: VectorSearchSettings;
    vectorData: VectorData[] = [];
    private genAI: GoogleGenAI;
    private reloadInterval: number | null = null;

    async onload() {
        await this.loadSettings();
        await this.loadVectorData();
        this.genAI = new GoogleGenAI({ apiKey: this.settings.apiKey });

        this.registerView(
            VECTOR_SEARCH_VIEW_TYPE,
            (leaf) => new VectorSearchView(leaf, this)
        );

        this.addCommand({
            id: 'show-vector-search',
            name: '顯示向量搜尋',
            callback: () => {
                this.activateView();
            }
        });

        this.addCommand({
            id: 'reload-vectors',
            name: '重新載入向量資料',
            callback: async () => {
                await this.loadVectorData();
                new Notice('向量資料已重新載入');
            }
        });

        this.addSettingTab(new VectorSearchSettingTab(this.app, this));

        this.startAutoReload();
    }

    async onunload() {
        if (this.reloadInterval) {
            window.clearInterval(this.reloadInterval);
            this.reloadInterval = null;
        }
    }

    private async activateView() {
        const { workspace } = this.app;
        
        let leaf = workspace.getLeavesOfType(VECTOR_SEARCH_VIEW_TYPE)[0];
        
        if (!leaf) {
            const newLeaf = workspace.getRightLeaf(false);
            if (newLeaf) {
                await newLeaf.setViewState({
                    type: VECTOR_SEARCH_VIEW_TYPE,
                    active: true,
                });
                leaf = newLeaf;
            }
        }
        
        if (leaf) {
            workspace.revealLeaf(leaf);
        }
    }

    private startAutoReload() {
        this.reloadInterval = window.setInterval(async () => {
            await this.loadVectorData();
        }, 5 * 60 * 1000);
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }

    async loadVectorData() {
        try {
            const pluginPath = this.app.vault.configDir + '/plugins/vector-search';
            const vectorData = await this.app.vault.adapter.read(pluginPath + '/vectors.json');
            if (vectorData) {
                this.vectorData = JSON.parse(vectorData) as VectorData[];
                console.log('成功載入向量資料，共', this.vectorData.length, '筆');
            }
        } catch (error) {
            console.error('無法載入向量資料:', error);
            this.vectorData = [];
        }
    }

    async searchSimilarNotes(query: string) {
        console.log('開始搜尋:', query);
        const queryVector = await this.getEmbedding(query);
        console.log('查詢向量生成完成');
        const results = [];

        for (const data of this.vectorData) {
            const similarity = this.cosineSimilarity(
                queryVector,
                data.vector
            );
            
            console.log(`檔案 ${data.filename} 的相似度: ${similarity}`);
            
            if (similarity > this.settings.similarityThreshold) {
                results.push({
                    path: data.path,
                    filename: data.filename,
                    similarity
                });
            }
        }

        console.log('搜尋完成，找到', results.length, '個結果');
        return results.sort((a, b) => b.similarity - a.similarity);
    }

    async getEmbedding(text: string): Promise<number[]> {
        try {
            const response = await this.genAI.models.embedContent({
                model: 'gemini-embedding-exp-03-07',
                contents: text,
            });
            
            if (response.embeddings && response.embeddings.length > 0 && response.embeddings[0].values) {
                return response.embeddings[0].values;
            }
            throw new Error('無法獲取向量');
        } catch (error) {
            console.error('向量化失敗:', error);
            return Array(768).fill(0).map(() => Math.random());
        }
    }

    cosineSimilarity(vecA: number[], vecB: number[]): number {
        const dotProduct = vecA.reduce((sum, a, i) => sum + a * vecB[i], 0);
        const normA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
        const normB = Math.sqrt(vecB.reduce((sum, b) => sum + b * b, 0));
        return dotProduct / (normA * normB);
    }
}

class VectorSearchSettingTab extends PluginSettingTab {
    plugin: VectorSearchPlugin;

    constructor(app: App, plugin: VectorSearchPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        new Setting(containerEl)
            .setName('相似度閾值')
            .setDesc('設定搜尋結果的最小相似度（0-1）')
            .addSlider(slider => slider
                .setLimits(0, 1, 0.1)
                .setValue(this.plugin.settings.similarityThreshold)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.similarityThreshold = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Gemini API 金鑰')
            .setDesc('設定 Gemini API 金鑰')
            .addText(text => text
                .setPlaceholder('輸入您的 API 金鑰')
                .setValue(this.plugin.settings.apiKey)
                .onChange(async (value) => {
                    this.plugin.settings.apiKey = value;
                    (this.plugin as any).genAI = new GoogleGenAI({ apiKey: value });
                    await this.plugin.saveSettings();
                }));
    }
} 