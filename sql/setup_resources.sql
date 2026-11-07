-- CommunityConnect AI - Snowflake setup
-- Creates the resources table, loads verified Miami-Dade resources, and
-- creates the Cortex Search service used by the Flask backend.
--
-- Every record below was checked against the official source in SOURCE_URL
-- on VERIFIED_ON. Do not add organizations without a verifiable source.

CREATE DATABASE IF NOT EXISTS COMMUNITYCONNECT_DB;

CREATE TABLE IF NOT EXISTS COMMUNITYCONNECT_DB.PUBLIC.RESOURCES (
  ID INTEGER,
  NAME STRING,
  CATEGORY STRING,             -- 'Veteran Support' | 'Food Assistance' | 'Employment'
  SECONDARY_CATEGORY STRING,   -- optional second category
  DESCRIPTION STRING,
  CITY STRING,                 -- shown as "location" on resource cards
  SERVICE_AREA STRING,         -- 'Miami-Dade County' for the MVP
  PHONE STRING,
  WEBSITE STRING,
  SOURCE_URL STRING,
  VERIFIED_ON DATE,
  IS_DEMO BOOLEAN DEFAULT FALSE
);

INSERT INTO COMMUNITYCONNECT_DB.PUBLIC.RESOURCES (ID, NAME, CATEGORY, SECONDARY_CATEGORY, DESCRIPTION, CITY, SERVICE_AREA, PHONE, WEBSITE, SOURCE_URL, VERIFIED_ON, IS_DEMO) VALUES
(1, 'Bruce W. Carter Department of Veterans Affairs Medical Center', 'Veteran Support', NULL,
 'VA medical center providing primary care and specialty health services for Veterans, including mental health care, substance use treatment, caregiver support, social work, and homeless Veteran care. Open 24/7.',
 '1201 NW 16th Street, Miami, FL 33125', 'Miami-Dade County', '305-575-7000',
 'https://www.va.gov/miami-health-care/locations/bruce-w-carter-department-of-veterans-affairs-medical-center/',
 'https://www.va.gov/miami-health-care/locations/bruce-w-carter-department-of-veterans-affairs-medical-center/', '2026-11-07', FALSE),
(2, 'VA Miami Healthcare System - Homeless Veteran Care', 'Veteran Support', 'Food Assistance',
 'Helps Veterans who are homeless or at risk of homelessness with immediate food and shelter, transitional and permanent housing, job training and education, financial support to prevent homelessness, and addiction treatment. Call the National Call Center for Homeless Veterans to be connected with local providers.',
 'Miami, FL', 'Miami-Dade County', '877-424-3838',
 'https://www.va.gov/miami-health-care/health-services/homeless-veteran-care/',
 'https://www.va.gov/miami-health-care/health-services/homeless-veteran-care/', '2026-11-07', FALSE),
(3, 'CareerSource South Florida - Veterans Career Services', 'Employment', 'Veteran Support',
 'Veterans section with dedicated staff helping Veterans find employment: priority for training and placement, resume and cover letter help, interview advice, contact with employers, and eligibility determination for vocational rehabilitation and training.',
 'Miami, FL', 'Miami-Dade County', '305-594-7615',
 'https://www.careersourcesfl.com/veterans',
 'https://www.careersourcesfl.com/veterans', '2026-11-07', FALSE),
(4, 'CareerSource South Florida', 'Employment', NULL,
 'Workforce development board for Miami-Dade offering job search, career training opportunities, career advancement services, job fairs and workshops, and resume assistance through its career centers.',
 '7300 Corporate Center Drive, Suite 500, Miami, FL 33126', 'Miami-Dade County', '305-594-7615',
 'https://www.careersourcesfl.com/',
 'https://www.careersourcesfl.com/contact-us', '2026-11-07', FALSE),
(5, 'Feeding South Florida', 'Food Assistance', NULL,
 'Hunger-relief organization serving South Florida that provides food assistance (appointment needed) and partners with local nonprofit agencies. Client services line for Broward and Miami-Dade Counties.',
 'Serves Miami-Dade County (main warehouse: Pembroke Park, FL)', 'Miami-Dade County', '954-518-1857',
 'https://feedingsouthflorida.org/',
 'https://feedingsouthflorida.org/contact', '2026-11-07', FALSE),
(6, 'Florida DCF - Supplemental Nutrition Assistance Program (SNAP)', 'Food Assistance', NULL,
 'Federal food assistance program administered by the Florida Department of Children and Families that provides nutritional support for low-income individuals and families. Apply online through MyACCESS, at a Family Resource Center, or by mail or fax.',
 'Statewide program (available to Miami-Dade residents)', 'Miami-Dade County', '850-300-4323',
 'https://www.myflfamilies.com/services/public-assistance/supplemental-nutrition-assistance-program-snap',
 'https://www.myflfamilies.com/services/public-assistance/supplemental-nutrition-assistance-program-snap', '2026-11-07', FALSE);

-- Cortex Search service (RAG retrieval). Demo rows are excluded.
CREATE OR REPLACE CORTEX SEARCH SERVICE COMMUNITYCONNECT_DB.PUBLIC.RESOURCE_SEARCH
  ON SEARCH_TEXT
  ATTRIBUTES CATEGORY, SECONDARY_CATEGORY, SERVICE_AREA
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT ID, NAME, CATEGORY, SECONDARY_CATEGORY, DESCRIPTION, CITY, SERVICE_AREA, PHONE, WEBSITE, SOURCE_URL,
           NAME || '. Category: ' || CATEGORY || COALESCE(', ' || SECONDARY_CATEGORY, '') || '. ' || DESCRIPTION || ' Location: ' || CITY AS SEARCH_TEXT
    FROM COMMUNITYCONNECT_DB.PUBLIC.RESOURCES
    WHERE IS_DEMO = FALSE
  );

-- Quick check
-- SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('COMMUNITYCONNECT_DB.PUBLIC.RESOURCE_SEARCH',
--   '{"query":"veteran job and food","columns":["NAME","CATEGORY"],"limit":5}');
