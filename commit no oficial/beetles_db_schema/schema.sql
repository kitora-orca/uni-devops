--
-- PostgreSQL database dump
--

\restrict wKGzByBrPgpdTtvcesj7EaLoBYyPBrye4hECosrpVQx3Qk4UzbWSCO6xXbkzU1L

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: beetle_species; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.beetle_species (
    species_id bigint NOT NULL,
    species_name character varying(200) NOT NULL
);


--
-- Name: beetle_species_species_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.beetle_species_species_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: beetle_species_species_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.beetle_species_species_id_seq OWNED BY public.beetle_species.species_id;


--
-- Name: catch; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catch (
    catch_id bigint NOT NULL,
    expedition_id bigint NOT NULL,
    species_id bigint NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT check_quantity CHECK ((quantity > 0))
);


--
-- Name: catch_catch_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catch_catch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catch_catch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catch_catch_id_seq OWNED BY public.catch.catch_id;


--
-- Name: expeditions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expeditions (
    expedition_id bigint NOT NULL,
    team_id bigint NOT NULL,
    place_id bigint NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone NOT NULL,
    CONSTRAINT check_expedition_time CHECK ((end_time >= start_time))
);


--
-- Name: expeditions_expedition_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expeditions_expedition_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expeditions_expedition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expeditions_expedition_id_seq OWNED BY public.expeditions.expedition_id;


--
-- Name: places; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.places (
    place_id bigint NOT NULL,
    place_name character varying(200) NOT NULL
);


--
-- Name: places_place_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.places_place_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: places_place_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.places_place_id_seq OWNED BY public.places.place_id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teams (
    team_id bigint NOT NULL,
    team_name character varying(100) NOT NULL
);


--
-- Name: teams_team_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.teams_team_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: teams_team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.teams_team_id_seq OWNED BY public.teams.team_id;


--
-- Name: beetle_species species_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.beetle_species ALTER COLUMN species_id SET DEFAULT nextval('public.beetle_species_species_id_seq'::regclass);


--
-- Name: catch catch_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catch ALTER COLUMN catch_id SET DEFAULT nextval('public.catch_catch_id_seq'::regclass);


--
-- Name: expeditions expedition_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expeditions ALTER COLUMN expedition_id SET DEFAULT nextval('public.expeditions_expedition_id_seq'::regclass);


--
-- Name: places place_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places ALTER COLUMN place_id SET DEFAULT nextval('public.places_place_id_seq'::regclass);


--
-- Name: teams team_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams ALTER COLUMN team_id SET DEFAULT nextval('public.teams_team_id_seq'::regclass);


--
-- Name: beetle_species beetle_species_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.beetle_species
    ADD CONSTRAINT beetle_species_pkey PRIMARY KEY (species_id);


--
-- Name: beetle_species beetle_species_species_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.beetle_species
    ADD CONSTRAINT beetle_species_species_name_key UNIQUE (species_name);


--
-- Name: catch catch_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catch
    ADD CONSTRAINT catch_pkey PRIMARY KEY (catch_id);


--
-- Name: expeditions expeditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expeditions
    ADD CONSTRAINT expeditions_pkey PRIMARY KEY (expedition_id);


--
-- Name: places places_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT places_pkey PRIMARY KEY (place_id);


--
-- Name: places places_place_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.places
    ADD CONSTRAINT places_place_name_key UNIQUE (place_name);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (team_id);


--
-- Name: teams teams_team_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_team_name_key UNIQUE (team_name);


--
-- Name: catch unique_expedition_species; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catch
    ADD CONSTRAINT unique_expedition_species UNIQUE (expedition_id, species_id);


--
-- Name: catch fk_catch_expedition; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catch
    ADD CONSTRAINT fk_catch_expedition FOREIGN KEY (expedition_id) REFERENCES public.expeditions(expedition_id) ON DELETE CASCADE;


--
-- Name: catch fk_catch_species; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catch
    ADD CONSTRAINT fk_catch_species FOREIGN KEY (species_id) REFERENCES public.beetle_species(species_id) ON DELETE RESTRICT;


--
-- Name: expeditions fk_expedition_place; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expeditions
    ADD CONSTRAINT fk_expedition_place FOREIGN KEY (place_id) REFERENCES public.places(place_id);


--
-- Name: expeditions fk_expedition_team; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expeditions
    ADD CONSTRAINT fk_expedition_team FOREIGN KEY (team_id) REFERENCES public.teams(team_id);


--
-- PostgreSQL database dump complete
--

\unrestrict wKGzByBrPgpdTtvcesj7EaLoBYyPBrye4hECosrpVQx3Qk4UzbWSCO6xXbkzU1L

