import logging
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import json
from datetime import datetime, timedelta
import os
import traceback

# Get logger
logger = logging.getLogger('ai_news_scraper.youtube')

# Resto de tus funciones de YouTube tal como las definiste...
def build_youtube_client(api_key):
    """
    Construye y devuelve un cliente de la API de YouTube.
    
    Args:
        api_key (str): Clave de API de YouTube
        
    Returns:
        object: Cliente de la API de YouTube
    """
    try:
        if not api_key or not isinstance(api_key, str):
            logger.error(f"Invalid YouTube API key: {api_key}")
            return None

        youtube = build('youtube', 'v3', developerKey=api_key)
        logger.info("YouTube API client created successfully")
        return youtube
    except Exception as e:
        logger.error(f"Failed to create YouTube API client: {str(e)}")
        raise


def get_channel_id(youtube, channel_name):
    """
    Obtiene el ID del canal a partir del nombre del canal.
    
    Args:
        youtube (object): Cliente de la API de YouTube
        channel_name (str): Nombre del canal
        
    Returns:
        str: ID del canal o None si no se encuentra
    """
    try:
        request = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id',
            maxResults=1
        )
        response = request.execute()
        
        if response['items']:
            channel_id = response['items'][0]['id']['channelId']
            logger.info(f"Found channel ID for '{channel_name}': {channel_id}")
            return channel_id
        
        logger.warning(f"No channel found for name '{channel_name}'")
        return None
    except Exception as e:
        logger.error(f"Error getting channel ID for '{channel_name}': {str(e)}")
        return None


def get_recent_videos(youtube, channel_id, max_results=50, days_back=7):
    """
    Obtiene videos recientes del canal publicados en los últimos X días.
    
    Args:
        youtube (object): Cliente de la API de YouTube
        channel_id (str): ID del canal
        max_results (int): Número máximo de resultados
        days_back (int): Cuando contar los 7 dias
        
    Returns:
        list: Lista de videos con información
    """
    try:
        request = youtube.search().list(
            channelId=channel_id,
            order='date',
            part='snippet',
            maxResults=max_results,
            type='video'
        )
        response = request.execute()
        
        videos = []
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for item in response['items']:
            published_at = datetime.strptime(
                item['snippet']['publishedAt'], 
                '%Y-%m-%dT%H:%M:%SZ'
            )
            
            if published_at >= cutoff_date:
                video = {
                    'title': item['snippet']['title'],
                    'video_id': item['id']['videoId'],
                    'published_at': item['snippet']['publishedAt']
                }
                videos.append(video)
        
        logger.info(f"Found {len(videos)} videos from the last {days_back} days for channel {channel_id}")
        return videos
    except Exception as e:
        logger.error(f"Error getting videos for channel {channel_id}: {str(e)}")
        return []


def download_subtitles(video_id, languages=['es', 'en'], output_dir='subtitles'):
    """
    Descarga subtítulos para un video en los idiomas especificados.
    
    Args:
        video_id (str): ID del video
        languages (list): Lista de códigos de idioma
        output_dir (str): Directorio de salida
        
    Returns:
        dict: Resultados para cada idioma
    """
    try:
        # Crear directorio si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created directory: {output_dir}")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        results = {}
        
        for language in languages:
            try:
                transcript = transcript_list.find_transcript([language])
                subtitles = transcript.fetch()
                
                # Guardar en formato JSON
                filename = f'{output_dir}/{video_id}_{language}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(subtitles, f, ensure_ascii=False, indent=2)
                
                results[language] = 'Success'
                logger.info(f"Downloaded {language} subtitles for video {video_id}")
                
            except Exception as e:
                results[language] = f'Failed: {str(e)}'
                logger.warning(f"Failed to download {language} subtitles for video {video_id}: {str(e)}")
        
        return results
        
    except Exception as e:
        error_msg = f"Failed to get any subtitles for video {video_id}: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg}


def process_channel(youtube, channel_name, max_videos=50, languages=['es', 'en'], days_back=7):
    """
    Procesa videos de un canal dentro del período de tiempo especificado.
    
    Args:
        youtube (object): Cliente de la API de YouTube
        channel_name (str): Nombre del canal
        max_videos (int): Número máximo de videos
        languages (list): Lista de idiomas para los subtítulos
        days_back (int): Días hacia atrás para filtrar
        
    Returns:
        list: Resultados del procesamiento
    """
    try:
        logger.info(f"Processing channel: {channel_name}")
        
        # Obtener ID del canal
        channel_id = get_channel_id(youtube, channel_name)
        if not channel_id:
            error_msg = f"Channel not found: {channel_name}"
            logger.warning(error_msg)
            return error_msg

        # Obtener videos recientes
        videos = get_recent_videos(youtube, channel_id, max_videos, days_back)
        
        if not videos:
            msg = f"No videos found in the last {days_back} days for channel: {channel_name}"
            logger.info(msg)
            return msg
        
        results = []
        for video in videos:
            try:
                result = {
                    'title': video['title'],
                    'video_id': video['video_id'],
                    'published_at': video['published_at'],
                    'subtitles': download_subtitles(video['video_id'], languages)
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing video {video['video_id']}: {str(e)}")
        
        # Guardar resultados en un archivo JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'results_{timestamp}.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved processing results to {results_file}")
        return results
        
    except Exception as e:
        error_msg = f"Error processing channel {channel_name}: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return error_msg


def clean_subtitle_text(text):
    """
    Limpia el texto de los subtítulos.
    
    Args:
        text (str): Texto a limpiar
        
    Returns:
        str: Texto limpio
    """
    try:
        import re
        
        # Reemplazar saltos de línea con espacios
        cleaned_text = text.replace('\n', ' ')
        # Reemplazar barras invertidas escapadas
        cleaned_text = cleaned_text.replace('\\', '')
        # Reemplazar múltiples espacios con uno solo
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    except Exception as e:
        logger.error(f"Error cleaning subtitle text: {str(e)}")
        return text


def get_video_transcript(video_id):
    """
    Obtiene la transcripción completa de un video.
    
    Args:
        video_id (str): ID del video
        
    Returns:
        tuple: (texto completo, idioma) o (None, None) si falla
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Intentar con subtítulos manuales primero
        try:
            transcript = transcript_list.find_manually_created_transcript()
        except:
            # Si no hay subtítulos manuales, probar con cualquier idioma disponible
            transcript = transcript_list.find_transcript(['en', 'es'])
        
        subtitles = transcript.fetch()
        language = transcript.language
        
        # Obtener texto de cada entrada de subtítulos
        subtitle_texts = [entry['text'] for entry in subtitles]
        
        # Limpiar cada segmento de texto
        cleaned_texts = [clean_subtitle_text(text) for text in subtitle_texts]
        
        # Unir todos los segmentos de texto limpios con espacios
        full_text = ' '.join(cleaned_texts).strip()
        
        logger.info(f"Successfully retrieved transcript for video {video_id} in {language}")
        return full_text, language
    
    except Exception as e:
        logger.error(f"Failed to get transcript for video {video_id}: {str(e)}")
        return None, None


def process_youtube_channels(api_key, channel_names, max_videos=5, days_back=7):
    """
    Procesa videos de múltiples canales y los combina en un solo CSV.
    
    Args:
        youtube (object): Cliente de la API de YouTube
        channel_names (list): Lista de nombres de canales
        max_videos (int): Máximo de videos por canal
        days_back (int): Solo incluir videos de los últimos X días
        
    Returns:
        DataFrame o str: DataFrame con los datos o mensaje de error
    """
    try:
        logger.info(f"Processing {len(channel_names)} channels: {', '.join(channel_names)}")
        
        youtube = build_youtube_client(api_key)

        # Lista para almacenar datos de todos los canales
        all_data = []
        
        # Procesar cada canal
        for channel_name in channel_names:
            try:
                logger.info(f"Processing channel: {channel_name}")
                
                # Obtener ID del canal
                channel_id = get_channel_id(youtube, channel_name)
                if not channel_id:
                    logger.warning(f"Channel not found: {channel_name}")
                    continue

                # Obtener videos de los últimos X días
                videos = get_recent_videos(youtube, channel_id, max_videos, days_back)
                
                if not videos:
                    logger.info(f"No videos found in the last 7 days for channel: {channel_name}")
                    continue
                
                # Procesar cada video
                for video in videos:
                    try:
                        video_id = video['video_id']
                        title = video['title']
                        date = datetime.strptime(video['published_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        # Obtener transcripción
                        full_text, language = get_video_transcript(video_id)
                        
                        if full_text:
                            # Generar resumen (descomentado cuando se implemente)
                            try:
                                summary = "not summary yet"  # summarize_with_openai(full_text)
                                
                                # Añadir a la lista de datos con el nombre del canal
                                all_data.append({
                                    'Title': title,
                                    'Date': date,
                                    'Link': video_url,
                                    'Summary': summary,
                                    'Source': channel_name,
                                    'Language': language
                                })
                                
                                logger.info(f"Successfully processed video: {title}")
                            except Exception as e:
                                logger.error(f"Error generating summary for video {video_id}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error processing video {video.get('video_id', 'unknown')}: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error processing channel {channel_name}: {str(e)}")
        
        # Si no se recopiló ningún dato
        if not all_data:
            msg = "No videos found for any of the specified channels"
            logger.warning(msg)
            return msg
                
        # # Crear DataFrame y guardar como CSV
        # df = pd.DataFrame(all_data)
        # df = df[['Title', 'Date', 'Link', 'Summary', 'Source', 'Language']]
        
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # csv_filename = f'multi_channel_subtitles_{timestamp}.csv'
        # df.to_csv(csv_filename, index=False, encoding='utf-8')
        
        # logger.info(f"Successfully saved data to {csv_filename}. Processed {len(all_data)} videos.")
        return all_data
        
    except Exception as e:
        error_msg = f"Error processing multiple channels: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return error_msg
