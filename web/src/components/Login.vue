<template>
  <div class="login-container">
    <div class="login-form">
      <h2>多智能体金融分析平台</h2>
      <Form ref="form" :model="formData" :rules="rules">
        <FormItem prop="username">
          <Input type="text" v-model="formData.username" placeholder="用户名" size="large">
            <Icon type="ios-person-outline" slot="prepend"></Icon>
          </Input>
        </FormItem>
        <FormItem prop="password">
          <Input type="password" v-model="formData.password" placeholder="密码" size="large">
            <Icon type="ios-lock-outline" slot="prepend"></Icon>
          </Input>
        </FormItem>
        <FormItem>
          <Button type="primary" @click="handleLogin" long size="large" :loading="loading">登录</Button>
        </FormItem>
      </Form>
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Login',
  data() {
    return {
      formData: {
        username: '',
        password: ''
      },
      rules: {
        username: [
          { required: true, message: '用户名不能为空', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '密码不能为空', trigger: 'blur' }
        ]
      },
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      this.$refs.form.validate(async (valid) => {
        if (valid) {
          this.loading = true
          this.error = ''
          
          try {
            const response = await axios.post('/api/auth/login', {
              username: this.formData.username,
              password: this.formData.password
            })
            
            // 存储token和过期时间
            localStorage.setItem('session_token', response.data.token)
            localStorage.setItem('token_expires', response.data.expires_at)
            
            // 跳转到主页面
            this.$router.push('/')
          } catch (error) {
            if (error.response && error.response.status === 401) {
              this.error = '用户名或密码错误'
            } else {
              this.error = '登录失败，请稍后重试'
            }
          } finally {
            this.loading = false
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.login-form h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.error-message {
  color: #ed4014;
  text-align: center;
  margin-top: 15px;
}
</style>
