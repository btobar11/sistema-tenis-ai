
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = 'https://hexpbbbsqkgowbrrorjt.supabase.co'
const SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhleHBiYmJzcWtnb3dicnJvcmp0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODkzNTM5MywiZXhwIjoyMDg0NTExMzkzfQ.8UwCEzeADaQHihrARPYXn_d3DvVo1WcQR5PDxXM7c68'

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    auth: {
        autoRefreshToken: false,
        persistSession: false
    }
})

async function createVerifiedUser() {
    const email = 'admin@edgeset.com'
    const password = 'EdgesetAdmin123!'

    console.log(`Creating verified user: ${email}...`)

    const { data, error } = await supabase.auth.admin.createUser({
        email,
        password,
        email_confirm: true // Force confirmation
    })

    if (error) {
        console.error('Error creating user:', error.message)
        // If user already exists, try to update verify status?
        if (error.message.includes('already registered')) {
            console.log('User exists, attempting to confirm email manually...')
            // We can search for the user ID if needed, but for now just tell user.
        }
        return
    }

    console.log('User created successfully!')
    console.log('ID:', data.user.id)
    console.log('Email:', data.user.email)
    console.log('Password:', password)
    console.log('\nYou can now login with these credentials immediately.')
}

createVerifiedUser()
