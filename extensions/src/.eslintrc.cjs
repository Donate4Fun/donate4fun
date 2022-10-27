module.exports = {
    "env": {
        "browser": true,
        "es2021": true
    },
    "extends": ["eslint:recommended", "plugin:no-unsanitized/DOM"],
    "overrides": [
    ],
    "parserOptions": {
        "ecmaVersion": "latest",
        "sourceType": "module"
    },
    "rules": {
        "no-mixed-spaces-and-tabs": "off",
        "no-unused-vars": "off",
        "no-undef": "off",
    }
}
