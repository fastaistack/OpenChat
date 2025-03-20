<p align="right">
  中文 | <a href="./README.en.md">English</a> 


这里是 OpenChat 官方发布的客户端安装包，基于MIT协议开源，支持多平台快速安装使用。对于大多数用户而言，推荐直接使用我们提供的官方版本，安装简单方便，并确保能够体验最新最全的功能。你可以在下方链接中选择适合你设备的安装包进行下载：

### 客户端下载
<table style="width: 100%">
  <tr>
    <td width="25%" align="center">
      <b>Windows</b>
    </td>
    <td width="25%" align="center">
      <b>MacOS</b>
    </td>
    
  </tr>
  <tr style="text-align: center">
    <td align="center" valign="middle">
      <a href='https://metabrain.oss-cn-beijing.aliyuncs.com/openchat/OpenChatSetup.exe'>
        <img src='./data/images/windows.png' style="height:30px; width: 30px" />
        <br />
        <b>Setup.exe</b>
      </a>
    </td>
    <td align="center" valign="middle">
      <a href='https://metabrain.oss-cn-beijing.aliyuncs.com/openchat/OpenChat.dmg'>
        <img src='./data/images/MAC.png' style="height:35px; width: 35px" />
        <br />
        <b>Intel</b>
      </a>
    </td>
    
    
  </tr>
</table>



---


# OpenChat - 你的一站式AI平台



OpenChat为客户端应用，提供一种基于大模型对话式交互模式，可以让用户很轻松的使用多种 AI 大模型，进行知识问答、网络信息检索、知识库以及文档对话等功能。

![](./data/images/intro/主页.png)

---

## 功能亮点

### 🚀 **智能 AI 助手平台**  

- 🌐 **兼容主流云端大模型**：如 OpenAI、Deepseek、硅基流动等  
- 🔗 **集成热门 AI 平台**：腾讯云、百度千帆云、Kimi Ai、智谱清言等  
- 🖥 **支持本地化模型部署**：适配 Ollama，服务器部署等本地运行方案  

### 🧠 **多功能智能助手**  
- 🤖 **智能助手应用**：集成Kimi，密塔AI搜索，文心一言，豆包等应用，让你一站式访问国内多个大模型平台
- 🔍 **敏感词检测**：精准识别敏感内容，确保文本合规  
- 📚 **知识问答**：智能解析各类问题，快速提供可靠解答  

### 🌍 **强大信息检索与知识管理**  
- 🔗 **网络信息检索**：实时查找最新数据，助力决策分析  
- 📖 **智能知识库**：个性化知识存储，便捷管理、随时调用  
- 📝 **文档对话**：支持文本、PDF、Office 交互式问答，高效阅读  

###  🧩 **实用工具与扩展功能**  
- 🔎 **智能搜索**：快速定位信息，提高工作效率  
- 🌐 **多模态支持**：文本、图片、文档等多类型输入处理  
- 📤 **内容管理与分享**：便捷整理，轻松共享知识  

### ✨ **卓越体验，畅快使用**  
- 🖥 **跨平台支持**：适配 Windows、Mac  
- ⚡ **即装即用**：无需复杂配置，开箱即用  
- 📑 **Markdown 解析**，文档呈现更清晰  
- 🚀 **高效稳定**：强大性能保障流畅体验
- 💡 **多模型协同交互**，不同视角助力深入分析  

<br>



### 📃 即将实现的功能

- [x] 多模型结果对比，获取多样化视角
- [x] 添加智能助手应用
- [x] 个性化数据备份
- [x] 敏感词检测功能更新
- [x] 全模型联网支持 
- [x] 网络检索功能更新
- [x] 知识库与文档对话功能更新
- [x] 首个正式版本发布
- [x] 持续改进与性能优化
- [ ] 自定义提示词
- [ ] 沉浸式翻译
- [ ] AI代码辅助
- [ ] 个性化智能体


更多功能敬请期待........

---

## 💻  配置与使用

### 1. 配置要求
内存：8GB以上
系统：Windows10/11 64位 & MacOS系统（Intel芯片）
### 2. 安装
#### 步骤1：下载OpenChat安装包
* OpenChat使用指南（本文档），提供下载、安装、操作指南；
* OpenChat安装包（Windows），OpenChatSetup.exe，客户端软件；
* OpenChat安装包（Apple_Intel芯片），OpenChat.dmg，客户端软件 ；

#### 步骤2：OpenChat客户端安装
完成应用程序（OpenChatSetup.exe）下载后，双击文件并同意用户使用协议，选择安装路径（自定义安装路径X:\\...\OpenChat），等待OpenChat自动安装程序完成。

Mac版OpenChat.dmg打开后将看到OpenChat.app，将其拖动到应用文件夹下即可使用。由于MacOS系统的安全防护机制打开时如出现风险提示，选择信任该程序，如出现因为无法验证开发者无法打开的问题，可重新双击打开或者在系统与偏好中安全性选项卡下点仍要打开。

### 3. 使用

关于客户端配置流程，程序具体功能的讲解和使用说明，请参照 <a href="./doc/intro/使用指南.md">OpenChat使用指南</a> 。

<br>

---

## 📦 打包与部署

本项目支持 **macOS** 和 **Windows** 的打包与分发，以下是基本的打包步骤。

### 🍎 macOS 打包指南

1. **环境准备**：确保 Python 3.10 及必要依赖已安装。
2. **代码调整**：适配 macOS 系统，修改路径、权限等。
3. **使用 PyInstaller 进行打包**：
   ```sh
   pyinstaller --clean --onedir --windowed --name "OpenChat" \
     --add-data "pkg:pkg" \
     --add-data "assets:assets" \
     --osx-bundle-identifier com.example.openchat \
     --hidden-import=imghdr \
     yuanchat.py
   ```
4. **手动补充依赖**：将缺失的 `site-packages` 依赖复制到 `Frameworks` 目录。
5. **创建 DMG 安装包**（可选）：
   ```sh
   hdiutil create -volname "OpenChat" -srcfolder "dist/OpenChat.app" -ov -format UDBZ "OpenChat.dmg"
   ```

📄 **详细 macOS 版本适配和打包指南** 👉 [Mac 版打包指南](doc/packaging/mac适配打包指南.md)



### 💻 Windows 打包指南

1. **安装 Python 及依赖环境**（推荐 3.10.11/3.10.12 版本）。
2. **创建虚拟环境并安装依赖**：
   ```sh
   pip install virtualenv
   virtualenv venv --python=python3.10.11
   pip install -r requirements.txt
   ```
3. **调整 Python 依赖**：
   - 修改 `pypandoc` 和 `pytesseract` 相关代码。
   - 将 `nltk_data` 放入 `venv/Lib` 目录。
4. **使用 PyInstaller 生成可执行文件**：
   ```sh
   pyinstaller -D openchat.py
   pyinstaller openchat.spec
   ```
5. **运行 `openchat.exe` 测试依赖**，手动补充 `_internal` 目录中的缺失依赖。
6. **使用 Inno Setup 生成安装包**（需安装 [Inno Setup Compiler](https://jrsoftware.org/isdl.php)）。
7. **执行 `openchatsetup.iss` 构建最终安装包**。

📄 **详细 Windows 打包指南** 👉 [Windows 版打包指南](doc/packaging/windows打包指南.md)


<br>

### 📌 说明
- **建议所有平台使用 Python 3.10 并通过 venv 进行隔离**。
- **如果打包后缺少依赖，请检查 `site-packages` 并手动补充**。
- **Windows 版本建议使用 Inno Setup 进行安装包封装**。
- **对于 Mac 和 Windows，可使用代码签名提升安全性**。




