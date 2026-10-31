import React, { useState } from 'react';
import GlideSelect from './GlideSelect';

export const DEGREE_OPTIONS = [
  { value: 'B.Tech', label: 'B.Tech / B.E.', tag: 'Engineering' },
  { value: 'BCA', label: 'BCA / B.Sc CS', tag: 'CS / IT' },
  { value: 'M.Tech', label: 'M.Tech / M.E.', tag: 'Postgrad' },
  { value: 'MCA', label: 'MCA / M.Sc', tag: 'Postgrad' },
  { value: 'B.Des', label: 'B.Des / Design', tag: 'Product/UI' },
  { value: 'Other', label: 'Other Degree', tag: 'Open' }
];

export const YEARS_BY_DEGREE = {
  'B.Tech': [
    { value: '1', label: '1st Year', tag: 'UG' },
    { value: '2', label: '2nd Year', tag: 'UG' },
    { value: '3', label: '3rd Year', tag: 'Pre-Final' },
    { value: '4', label: '4th Year', tag: 'Final Year' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ],
  'BCA': [
    { value: '1', label: '1st Year', tag: 'UG' },
    { value: '2', label: '2nd Year', tag: 'Pre-Final' },
    { value: '3', label: '3rd Year', tag: 'Final Year' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ],
  'M.Tech': [
    { value: '1', label: '1st Year (PG-1)', tag: 'Postgrad' },
    { value: '2', label: '2nd Year (Final Year)', tag: 'Final Year' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ],
  'MCA': [
    { value: '1', label: '1st Year (PG-1)', tag: 'Postgrad' },
    { value: '2', label: '2nd Year (Final Year)', tag: 'Final Year' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ],
  'B.Des': [
    { value: '1', label: '1st Year', tag: 'Foundation' },
    { value: '2', label: '2nd Year', tag: 'Studio' },
    { value: '3', label: '3rd Year', tag: 'Pre-Final' },
    { value: '4', label: '4th Year', tag: 'Final Year' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ],
  'Other': [
    { value: '1', label: '1st Year', tag: 'Year 1' },
    { value: '2', label: '2nd Year', tag: 'Year 2' },
    { value: '3', label: '3rd Year', tag: 'Year 3' },
    { value: '4', label: '4th Year', tag: 'Year 4' },
    { value: 'grad', label: 'Graduated / Working', tag: 'Alumni' }
  ]
};

export const STREAMS_BY_DEGREE = {
  'B.Tech': [
    { value: 'CSE', label: 'Computer Science (CSE)', tag: 'Popular' },
    { value: 'IT', label: 'Information Tech (IT)', tag: 'Tech' },
    { value: 'AI', label: 'AI & Data Science', tag: 'Hot' },
    { value: 'ECE', label: 'Electronics & Comm (ECE)', tag: 'Hardware' },
    { value: 'Mechanical', label: 'Mechanical & Robotics', tag: 'Core' },
    { value: 'BioTech', label: 'Biotech & Healthcare', tag: 'MedTech' },
    { value: 'General', label: 'All Engineering Streams', tag: 'Universal' }
  ],
  'BCA': [
    { value: 'BCA-General', label: 'Computer Applications (BCA)', tag: 'Software' },
    { value: 'BSc-CS', label: 'B.Sc Computer Science', tag: 'Algorithms' },
    { value: 'DataScience', label: 'Data Science & Analytics', tag: 'Analytics' },
    { value: 'Cloud-Web', label: 'Web & Cloud Development', tag: 'Full Stack' },
    { value: 'General', label: 'All Computing Streams', tag: 'Universal' }
  ],
  'M.Tech': [
    { value: 'MTech-CSE', label: 'Advanced Computer Science', tag: 'Research' },
    { value: 'MTech-AI', label: 'Artificial Intelligence & ML', tag: 'Deep Tech' },
    { value: 'MTech-VLSI', label: 'VLSI & Embedded Systems', tag: 'Hardware' },
    { value: 'MTech-Cyber', label: 'Cybersecurity & Networks', tag: 'Security' },
    { value: 'General', label: 'All PG Engineering', tag: 'Postgrad' }
  ],
  'MCA': [
    { value: 'MCA-General', label: 'Master of Computer Apps', tag: 'Enterprise' },
    { value: 'MSc-CS', label: 'M.Sc Computer Science', tag: 'Computing' },
    { value: 'MSc-Data', label: 'M.Sc Data Science & AI', tag: 'Analytics' },
    { value: 'General', label: 'All PG Computing Streams', tag: 'Universal' }
  ],
  'B.Des': [
    { value: 'UIUX', label: 'UI / UX & Digital Products', tag: 'Product' },
    { value: 'Interaction', label: 'Interaction & HCI', tag: 'Tech Design' },
    { value: 'Visual', label: 'Communication & Visual', tag: 'Media' },
    { value: 'General', label: 'All Design Disciplines', tag: 'Universal' }
  ],
  'Other': [
    { value: 'CSE', label: 'Software & Technology', tag: 'Tech' },
    { value: 'General', label: 'Open to All Streams', tag: 'Universal' }
  ]
};

export const CITY_OPTIONS = [
  { value: 'Bengaluru|Karnataka', label: 'Bengaluru', tag: 'Karnataka' },
  { value: 'Hyderabad|Telangana', label: 'Hyderabad', tag: 'Telangana' },
  { value: 'Pune|Maharashtra', label: 'Pune', tag: 'Maharashtra' },
  { value: 'New Delhi|Delhi', label: 'Delhi NCR', tag: 'Delhi' },
  { value: 'Mumbai|Maharashtra', label: 'Mumbai', tag: 'Maharashtra' },
  { value: 'Chennai|Tamil Nadu', label: 'Chennai', tag: 'Tamil Nadu' },
  { value: 'Any|Remote', label: 'Any City / Remote', tag: 'Virtual' }
];

export const MODE_OPTIONS = [
  { value: 'both', label: 'Both (All Events)', tag: 'Recommended' },
  { value: 'in-person', label: 'In-Person Only', tag: 'Local' },
  { value: 'online', label: 'Online Only', tag: 'Virtual' }
];

export const SORT_OPTIONS = [
  { value: 'fit', label: 'Best Fit Score', tag: 'Top Match' },
  { value: 'urgency', label: 'Closest Deadline', tag: 'Urgent' },
  { value: 'name', label: 'Alphabetical', tag: 'A - Z' }
];

export function ProfileSelectors({ degree, setDegree, stream, setStream, year, setYear }) {
  const currentYears = YEARS_BY_DEGREE[degree] || YEARS_BY_DEGREE['Other'];
  const currentStreams = STREAMS_BY_DEGREE[degree] || STREAMS_BY_DEGREE['Other'];

  const handleDegreeChange = (newDeg) => {
    setDegree(newDeg);
    const nextYears = YEARS_BY_DEGREE[newDeg] || YEARS_BY_DEGREE['Other'];
    const nextStreams = STREAMS_BY_DEGREE[newDeg] || STREAMS_BY_DEGREE['Other'];
    setYear(nextYears[0].value);
    setStream(nextStreams[0].value);
  };

  return (
    <div style={{ display: 'grid', gap: '1rem' }}>
      <GlideSelect
        options={DEGREE_OPTIONS}
        value={degree}
        onChange={handleDegreeChange}
        ariaLabel="Degree"
        menuWidth={260}
      />
      <GlideSelect
        options={currentStreams}
        value={stream}
        onChange={setStream}
        ariaLabel="Stream"
        menuWidth={280}
      />
      <GlideSelect
        options={currentYears}
        value={year}
        onChange={setYear}
        ariaLabel="Year of Study"
        menuWidth={250}
      />
    </div>
  );
}
