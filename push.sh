#!/bin/bash

# تنظیمات
BRANCH="main"
COMMIT_MSG="Auto-deploy: $(date +'%Y-%m-%d %H:%M:%S')"

# مرحله 1: افزودن تمام تغییرات
echo "📦 افزودن همه تغییرات..."
git add .

# مرحله 2: ساخت کامیت
echo "📝 ساخت کامیت با پیام: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# مرحله 3: پوش به مخزن
echo "🚀 پوش به GitHub در شاخه $BRANCH ..."
git push origin $BRANCH

echo "✅ همه چیز با موفقیت پوش شد."
