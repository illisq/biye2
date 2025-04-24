# LLM Fuzz Testing Framework

本项目是一个大型语言模型(LLM)的模糊测试框架，用于自动化发现和测试LLM的各种漏洞和边缘情况。

## 特性

- 支持多种LLM提供商 (OpenAI, Anthropic等)
- 自动化测试多种漏洞类型（幻觉、安全问题、提示注入等）
- 可配置的测试策略和变异器
- 完整的测试报告和日志

## 配置

1. 复制`.env.example`文件到`.env`并填入您的API密钥和配置选项:
   ```
   cp .env.example .env
   ```

2. 根据需要修改`config/config.yaml`文件中的配置:
   - 系统配置（日志级别、随机种子等）
   - API配置（模型选择、参数设置等）
   - 测试配置（漏洞类型、变异设置等）
   - 路径配置（模板目录、结果目录等）

## 使用方法

1. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

2. 运行测试:
   ```
   python main.py --config config/config.yaml
   ```

3. 查看报告:
   测试结果和报告将保存在配置文件指定的目录中。

## 贡献

欢迎提交问题和拉取请求。

## 许可

[MIT](LICENSE) 