<!-- Monorepo note added by script -->
**Note**: This project is part of the Pan-Sea monorepo. For monorepo-level setup and services overview, see `../README.md`.

# Pan-Sea Education Platform

A modern, intelligent classroom management platform built with Next.js that empowers teachers to start classes, engage students, and automatically generate comprehensive educational summaries with AI-powered insights.

## 🎓 Educational Focus

This platform is specifically designed for educational environments where teachers need to:
- Start and manage virtual or hybrid classes
- Track student engagement and participation
- Automatically generate detailed class summaries
- Document learning objectives and homework assignments
- Share insights with students and parents

## 🏗️ Project Structure

```
src/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx               # Root layout with educational branding
│   ├── page.tsx                 # Teacher Dashboard - main landing page
│   ├── meeting/[id]/           # Dynamic classroom pages (virtual classrooms)
│   │   └── page.tsx            # Individual classroom interface
│   └── summary/[id]/           # Class summary pages
│       └── page.tsx            # Individual class summary with educational insights
├── components/                  # Reusable UI components
│   └── meeting/                # Class-related components (renamed for consistency)
│       ├── CreateMeetingForm.tsx    # Create new class form with educational fields
│       ├── MeetingControls.tsx      # Class start/end controls with student management
│       └── MeetingSummaryDisplay.tsx # Display educational summaries
├── lib/                        # Utility functions and business logic
│   └── meeting-utils.ts        # Class operations, educational data management
└── types/                      # TypeScript type definitions
    └── meeting.ts              # Class and educational summary interfaces
```

## ✨ Educational Features

### 👩‍ For Teachers
- **Create Classes**: Form with subject, grade level, classroom, and student roster
- **Class Controls**: Start/end classes with real-time duration tracking and student engagement
- **Student Management**: Track attendance, participation, and engagement levels
- **Smart Summaries**: AI-generated summaries including topics, learning objectives, and homework

### 🎯 Class Management
- **Live Status**: Visual indicators for class status (scheduled/in-progress/completed)
- **Subject Organization**: Classes organized by subject, grade level, and teacher
- **Real-time Analytics**: Student engagement metrics and participation tracking
- **Educational Insights**: Automated detection of learning objectives achieved

### 📚 Educational Summaries Include:
- **Topics Discussed**: Detailed breakdown of lesson content
- **Learning Objectives**: Achievement tracking and assessment
- **Homework Assignments**: Automatically generated task lists
- **Student Participation**: Engagement metrics and insights
- **Announcements**: Important class and school communications
- **Next Class Preview**: Preparation notes for upcoming lessons

### 📱 Modern Educational Interface
- **Teacher-Friendly Design**: Clean, intuitive interface designed for educators
- **Educational Color Scheme**: Professional blue/green palette suitable for schools
- **Responsive Layout**: Works perfectly on classroom displays, tablets, and mobile devices
- **Educational Icons**: Subject-specific emojis and educational symbols throughout

## 🚀 Getting Started for Educators

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start the Educational Platform**
   ```bash
   npm run dev
   ```

3. **Access Teacher Dashboard**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📋 How Teachers Use the Platform

### Creating a Class
1. Click "➕ Create New Class" on the teacher dashboard
2. Enter class details:
   - Class title (e.g., "Introduction to Algebra")
   - Subject from dropdown (Math, Science, English, etc.)
   - Teacher name
   - Grade level (K-12)
   - Classroom number
3. Add student names to the roster
4. Click "🎓 Create Class" to set up the virtual classroom

### Managing Classes
1. Click "▶️ Start Class" to begin the lesson
2. Monitor live engagement metrics and student participation
3. Use quick actions for notes, attendance, and announcements
4. Click "⏹️ End Class & Generate Summary" when lesson concludes

### Educational Summaries
1. Completed classes automatically show "📝 Summary" button
2. AI-generated summaries include:
   - **Student attendance** and participation metrics
   - **Topics covered** with detailed breakdown
   - **Learning objectives** achieved during class
   - **Homework assignments** automatically formatted
   - **Class announcements** and important notes
   - **Next class preparation** recommendations

### Sharing and Collaboration
- **Print Summaries**: Professional format for physical distribution
- **Email Integration**: Send summaries to students and parents
- **Copy to Clipboard**: Easy integration with school management systems

## 🔮 Educational Enhancements Planned

### Advanced Teaching Features
- **Video Integration**: Record classes for absent students
- **Interactive Whiteboard**: Digital collaboration tools
- **Assignment Distribution**: Automatic homework delivery
- **Grade Integration**: Connect with gradebook systems
- **Parent Portal**: Summary sharing with families
- **Student Analytics**: Individual learning progress tracking

### AI-Powered Education Tools
- **Real Transcription**: Live speech-to-text for comprehensive notes
- **Learning Assessment**: Automatic evaluation of student understanding
- **Curriculum Alignment**: Match lessons to educational standards
- **Personalized Recommendations**: Suggest teaching strategies based on class data
- **Attendance Automation**: Facial recognition for automatic roll call

### School Integration
- **LMS Integration**: Canvas, Blackboard, Google Classroom compatibility
- **SIS Integration**: Student Information System connectivity
- **Calendar Sync**: Automatic schedule management
- **Report Generation**: Administrative summaries and analytics
- **Multi-Language Support**: International school compatibility

## 🎨 Educational Design System

The platform uses an education-focused design:
- **Colors**: Professional blue primary, educational green accents, warm yellows for engagement
- **Typography**: Clear, readable fonts optimized for educational content
- **Icons**: Educational emojis and symbols (🎓📚👩‍🏫📝) throughout
- **Layout**: Classroom-inspired design with teacher-centric navigation
- **Accessibility**: High contrast and screen reader friendly for inclusive education

## 🛠️ Educational Technology Stack

- **Framework**: Next.js 15 with App Router (optimized for educational workflows)
- **Language**: TypeScript (ensuring reliability for educational data)
- **Styling**: Tailwind CSS (educational design system)
- **State Management**: React hooks (real-time classroom state)
- **Routing**: Educational URL structure (/meeting/ for classes, /summary/ for reports)
- **Future**: WebRTC for video, AI APIs for smart summaries

## 📁 Key Educational Files

- `src/app/page.tsx` - Teacher dashboard with class management
- `src/app/meeting/[id]/page.tsx` - Virtual classroom interface
- `src/app/summary/[id]/page.tsx` - Educational summary reports
- `src/lib/meeting-utils.ts` - Educational business logic and class management
- `src/types/meeting.ts` - Educational TypeScript interfaces (Class, ClassSummary)
- `src/components/meeting/` - All educational UI components

## Educational Use Cases

- **K-12 Schools**: Elementary through high school classroom management
- **Higher Education**: University lecture and seminar management  
- **Training Centers**: Corporate and professional development classes
- **Online Tutoring**: One-on-one and small group educational sessions
- **Hybrid Learning**: Combination of in-person and remote education
- **Special Education**: Adaptive tools for diverse learning needs

This educational platform provides teachers with a comprehensive solution for modern classroom management, combining the convenience of digital tools with the pedagogical insights needed for effective teaching and learning.
